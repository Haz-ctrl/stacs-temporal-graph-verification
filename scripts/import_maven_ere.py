"""
Adapter for MAVEN-ERE temporal relations.

This script supports two workflows:

1. `train` / `valid` conversion for local verification:
   convert annotated temporal relations into canonical pairwise tasks.

2. `test` conversion for prediction generation:
   enumerate candidate mention/TIMEX pairs with empty gold labels so the
   existing baseline runner can emit pairwise predictions that can later be
   packed into a CodaLab submission.

The verification framework currently supports coarse temporal labels:
`BEFORE`, `AFTER`, `SIMULTANEOUS`, and `UNKNOWN`.

MAVEN-ERE uses a richer temporal inventory:
`BEFORE`, `OVERLAP`, `CONTAINS`, `SIMULTANEOUS`, `BEGINS-ON`, `ENDS-ON`.

By default we keep only relations already supported by the verifier and skip
interval relations. `OVERLAP` can optionally be coarsened into
`SIMULTANEOUS` when a larger but noisier slice is desired.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


SUPPORTED_TEMPORAL_LABELS = {"BEFORE", "SIMULTANEOUS"}
ALL_TEMPORAL_LABELS = (
    "BEFORE",
    "OVERLAP",
    "CONTAINS",
    "SIMULTANEOUS",
    "ENDS-ON",
    "BEGINS-ON",
)

# Default target relation counts for stratified sampling.
# SIMULTANEOUS is the scarce class; BEFORE is capped relative to it.
# None means "take all available".
DEFAULT_TARGET_COUNTS: Dict[str, Optional[int]] = {
    "SIMULTANEOUS": None,  # keep every EVENT-EVENT SIMULTANEOUS pair
    "BEFORE": None,  # capped via --before-multiplier relative to SIMULTANEOUS
}


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _choose_sentence_window(
    sent_a: int, sent_b: int, *, radius: int, max_index: int
) -> Tuple[int, int]:
    start = max(0, min(sent_a, sent_b) - radius)
    end = min(max_index, max(sent_a, sent_b) + radius)
    return start, end


def _surface_text_from_tokens(
    sentence_tokens: Sequence[str], offset: Sequence[int], fallback: str
) -> str:
    if len(offset) != 2:
        return fallback
    start, end = int(offset[0]), int(offset[1])
    if 0 <= start < end <= len(sentence_tokens):
        span = " ".join(sentence_tokens[start:end]).strip()
        if span:
            return span
    return fallback


def _event_mentions(record: Dict[str, Any]) -> List[Dict[str, Any]]:
    mentions: List[Dict[str, Any]] = []
    for event in record.get("events", []):
        event_id = str(event["id"])
        event_type = str(event.get("type", ""))
        for mention in event.get("mention", []):
            mentions.append(
                {
                    "node_id": event_id,
                    "kind": "EVENT",
                    "mention_id": str(mention["id"]),
                    "text": str(mention.get("trigger_word", "")).strip(),
                    "sent_id": int(mention["sent_id"]),
                    "offset": list(mention.get("offset", [])),
                    "type": event_type,
                    "chain_size": len(event.get("mention", [])),
                }
            )
    return mentions


def _timex_mentions(record: Dict[str, Any]) -> List[Dict[str, Any]]:
    mentions: List[Dict[str, Any]] = []
    for timex in record.get("TIMEX", []):
        mentions.append(
            {
                "node_id": str(timex["id"]),
                "kind": "TIME",
                "mention_id": str(timex["id"]),
                "text": str(timex.get("mention", "")).strip(),
                "sent_id": int(timex["sent_id"]),
                "offset": list(timex.get("offset", [])),
                "type": str(timex.get("type", "")),
                "chain_size": 1,
            }
        )
    return mentions


def _group_mentions_by_node(record: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for mention in _event_mentions(record) + _timex_mentions(record):
        grouped.setdefault(mention["node_id"], []).append(mention)
    return grouped


def _choose_anchor_pair(
    left_mentions: Sequence[Dict[str, Any]],
    right_mentions: Sequence[Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    ranked = sorted(
        (
            (
                abs(int(left["sent_id"]) - int(right["sent_id"])),
                int(left["sent_id"]),
                int(right["sent_id"]),
                str(left["mention_id"]),
                str(right["mention_id"]),
                left,
                right,
            )
            for left in left_mentions
            for right in right_mentions
        ),
        key=lambda item: item[:5],
    )
    if not ranked:
        raise ValueError("Cannot choose anchor pair from empty mention lists.")
    _, _, _, _, _, left_anchor, right_anchor = ranked[0]
    return left_anchor, right_anchor


def _label_for_anchor(record: Dict[str, Any], anchor: Dict[str, Any]) -> str:
    sent_id = int(anchor["sent_id"])
    tokens = list(record.get("tokens", []))
    fallback = str(anchor.get("text", "")).strip() or str(anchor["node_id"])
    if 0 <= sent_id < len(tokens):
        surface = _surface_text_from_tokens(
            tokens[sent_id], anchor.get("offset", []), fallback
        )
    else:
        surface = fallback
    return f"{surface} [{anchor['mention_id']}]"


def _prompt_for_pair(
    *,
    title: str,
    passage: str,
    left_label: str,
    right_label: str,
) -> str:
    lines: List[str] = []
    if title:
        lines.extend(["Title:", title, ""])
    lines.extend(
        [
            "Passage:",
            passage,
            "",
            "Determine the temporal relation between the following mentions.",
            f"- {left_label}",
            f"- {right_label}",
            "",
            "Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.",
        ]
    )
    return "\n".join(lines)


def _map_relation(raw_relation: str, *, coarsen_overlap: bool) -> Optional[str]:
    relation = raw_relation.strip().upper()
    if relation in SUPPORTED_TEMPORAL_LABELS:
        return relation
    if relation == "OVERLAP" and coarsen_overlap:
        return "SIMULTANEOUS"
    return None


def _build_task(
    *,
    record: Dict[str, Any],
    split: str,
    pair_index: int,
    source_node_id: str,
    target_node_id: str,
    source_anchor: Dict[str, Any],
    target_anchor: Dict[str, Any],
    relation: Optional[str],
    original_relation: str,
    category: str,
    context_radius: int,
) -> Dict[str, Any]:
    sentences = list(record.get("sentences", []))
    max_index = max(len(sentences) - 1, 0)
    start, end = _choose_sentence_window(
        int(source_anchor["sent_id"]),
        int(target_anchor["sent_id"]),
        radius=context_radius,
        max_index=max_index,
    )
    passage = " ".join(sentences[start : end + 1]).strip()
    title = str(record.get("title", "")).strip()
    left_label = _label_for_anchor(record, source_anchor)
    right_label = _label_for_anchor(record, target_anchor)
    task_id = f"maven_ere_{split}_{record['id']}_{pair_index:07d}"

    gold_relations: List[List[str]]
    if relation is None:
        gold_relations = []
    else:
        gold_relations = [[left_label, right_label, relation]]

    return {
        "id": task_id,
        "category": category,
        "question": _prompt_for_pair(
            title=title,
            passage=passage,
            left_label=left_label,
            right_label=right_label,
        ),
        "events": [left_label, right_label],
        "gold_relations": gold_relations,
        "expected_valid": True,
        "expected_consistent": True,
        "metadata": {
            "source_format": "maven_ere_temporal",
            "document_id": str(record["id"]),
            "split": split,
            "title": title,
            "original_relation": original_relation,
            "mapped_relation": relation,
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "source_node_kind": str(source_anchor["kind"]),
            "target_node_kind": str(target_anchor["kind"]),
            "source_mention_id": str(source_anchor["mention_id"]),
            "target_mention_id": str(target_anchor["mention_id"]),
            "source_type": str(source_anchor.get("type", "")),
            "target_type": str(target_anchor.get("type", "")),
            "source_chain_size": int(source_anchor.get("chain_size", 1)),
            "target_chain_size": int(target_anchor.get("chain_size", 1)),
            "sentence_start": start,
            "sentence_end": end,
        },
    }


def _is_event_node(node_id: str) -> bool:
    return str(node_id).startswith("EVENT_")


def convert_maven_ere_temporal_split(
    path: Path,
    *,
    split: str,
    category: str,
    context_radius: int,
    coarsen_overlap: bool,
    event_event_only: bool = True,
    before_multiplier: float = 2.0,
    max_tasks: int,
    seed: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Convert a MAVEN-ERE train/valid split into canonical pairwise tasks.

    Stratified sampling strategy
    -----------------------------
    Prior behaviour (global shuffle + truncate) produced heavily BEFORE-skewed
    outputs because BEFORE pairs outnumber SIMULTANEOUS ~99:1.  This version
    collects each relation type into its own pool, then:

      1. Takes ALL SIMULTANEOUS pairs (the scarce class, fully preserved).
      2. Samples BEFORE pairs up to ``before_multiplier * len(simultaneous_pool)``
         drawn uniformly at random (fixed seed).
      3. Merges and shuffles the result before writing.

    This yields a dataset where BEFORE / SIMULTANEOUS ≈ before_multiplier : 1,
    with a total size that is substantially larger than TempEval while remaining
    statistically meaningful for per-label analysis.

    EVENT-EVENT filtering
    ----------------------
    When ``event_event_only=True`` (default), relation pairs where either node
    is a TIMEX are dropped.  This keeps task context homogeneous and avoids
    time-expression surface forms (e.g. "1945") being treated as events.
    """
    rng = random.Random(seed)
    docs = _load_jsonl(path)

    # ── Phase 1: collect all valid pairs into per-relation pools ──────────────
    pools: Dict[str, List[Tuple[Dict[str, Any], str, str, str]]] = {
        "BEFORE": [],
        "SIMULTANEOUS": [],
    }
    skipped_relation_counts: Counter = Counter()
    event_ids_by_doc: Dict[str, set] = {}

    for record in docs:
        doc_id = str(record["id"])
        event_ids = {e["id"] for e in record.get("events", [])}
        event_ids_by_doc[doc_id] = event_ids
        grouped_mentions = _group_mentions_by_node(record)

        for relation_name, pairs in dict(record.get("temporal_relations", {})).items():
            mapped = _map_relation(relation_name, coarsen_overlap=coarsen_overlap)
            if mapped is None or mapped not in pools:
                skipped_relation_counts[relation_name] += len(pairs)
                continue

            for pair in list(pairs):
                if len(pair) != 2:
                    continue
                src_id, tgt_id = str(pair[0]), str(pair[1])

                # Optionally restrict to EVENT-EVENT pairs
                if event_event_only and not (
                    _is_event_node(src_id) and _is_event_node(tgt_id)
                ):
                    skipped_relation_counts[f"{relation_name}:timex_filtered"] += 1
                    continue

                if src_id not in grouped_mentions or tgt_id not in grouped_mentions:
                    skipped_relation_counts[f"{relation_name}:missing_node"] += 1
                    continue

                pools[mapped].append((record, src_id, tgt_id, relation_name))

    # ── Phase 2: stratified sampling ──────────────────────────────────────────
    rng.shuffle(pools["SIMULTANEOUS"])
    rng.shuffle(pools["BEFORE"])

    sim_pool = pools["SIMULTANEOUS"]
    bef_pool = pools["BEFORE"]

    n_sim = len(sim_pool)

    if n_sim == 0:
        # No SIMULTANEOUS pairs available: fall back to keeping all BEFORE pairs.
        # This preserves backward-compatible behaviour on datasets or test fixtures
        # that contain only BEFORE relations.
        sampled_pairs = list(bef_pool)
    else:
        n_bef_target = int(round(before_multiplier * n_sim))
        n_bef_sampled = min(n_bef_target, len(bef_pool))
        sampled_pairs = sim_pool + bef_pool[:n_bef_sampled]

    rng.shuffle(sampled_pairs)

    # Apply absolute task cap after stratification
    if max_tasks > 0:
        sampled_pairs = sampled_pairs[:max_tasks]

    # ── Phase 3: build task records ───────────────────────────────────────────
    tasks: List[Dict[str, Any]] = []
    kept_relation_counts: Counter[str] = Counter()

    for pair_index, (record, src_id, tgt_id, original_relation) in enumerate(
        sampled_pairs
    ):
        grouped_mentions = _group_mentions_by_node(record)
        mapped = _map_relation(original_relation, coarsen_overlap=coarsen_overlap)
        if mapped is None:
            raise ValueError(
                f"Sampled relation {original_relation!r} cannot be mapped."
            )
        source_anchor, target_anchor = _choose_anchor_pair(
            grouped_mentions[src_id],
            grouped_mentions[tgt_id],
        )
        tasks.append(
            _build_task(
                record=record,
                split=split,
                pair_index=pair_index,
                source_node_id=src_id,
                target_node_id=tgt_id,
                source_anchor=source_anchor,
                target_anchor=target_anchor,
                relation=mapped,
                original_relation=original_relation,
                category=category,
                context_radius=context_radius,
            )
        )
        kept_relation_counts[mapped] += 1

    total = len(tasks)
    label_fracs = {
        k: f"{v}/{total} ({v / total * 100:.1f}%)" if total else "0"
        for k, v in sorted(kept_relation_counts.items())
    }

    stats: Dict[str, Any] = {
        "split": split,
        "input_path": str(path),
        "num_documents": len(docs),
        "num_tasks": total,
        "before_multiplier": before_multiplier,
        "event_event_only": event_event_only,
        "pool_sizes": {"BEFORE": len(bef_pool), "SIMULTANEOUS": n_sim},
        "sampled_counts": dict(sorted(kept_relation_counts.items())),
        "label_fractions": label_fracs,
        "skipped_relation_counts": dict(sorted(skipped_relation_counts.items())),
    }
    return tasks, stats


def _mention_candidates_for_test(
    record: Dict[str, Any],
    *,
    include_timex: bool,
) -> List[Dict[str, Any]]:
    mentions = []
    for mention in record.get("event_mentions", []):
        mentions.append(
            {
                "node_id": str(mention["id"]),
                "kind": "EVENT",
                "mention_id": str(mention["id"]),
                "text": str(mention.get("trigger_word", "")).strip(),
                "sent_id": int(mention["sent_id"]),
                "offset": list(mention.get("offset", [])),
                "type": str(mention.get("type", "")),
                "chain_size": 1,
            }
        )
    if include_timex:
        mentions.extend(_timex_mentions(record))
    return mentions


def convert_maven_ere_test_candidates(
    path: Path,
    *,
    split: str,
    category: str,
    context_radius: int,
    include_timex: bool,
    sentence_window: int,
    max_docs: int = 0,
    max_tasks: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    docs = _load_jsonl(path)
    if max_docs > 0:
        docs = docs[:max_docs]

    tasks: List[Dict[str, Any]] = []
    stats: Dict[str, Any] = {
        "split": split,
        "input_path": str(path),
        "num_documents": len(docs),
        "num_tasks": 0,
        "pair_mode": "all"
        if sentence_window < 0
        else f"sentence_window_{sentence_window}",
        "include_timex": include_timex,
    }
    pair_index = 0

    for record in docs:
        mentions = _mention_candidates_for_test(record, include_timex=include_timex)
        for left in mentions:
            for right in mentions:
                if left["mention_id"] == right["mention_id"]:
                    continue
                if (
                    sentence_window >= 0
                    and abs(int(left["sent_id"]) - int(right["sent_id"]))
                    > sentence_window
                ):
                    continue
                pair_index += 1
                tasks.append(
                    _build_task(
                        record=record,
                        split=split,
                        pair_index=pair_index,
                        source_node_id=str(left["node_id"]),
                        target_node_id=str(right["node_id"]),
                        source_anchor=left,
                        target_anchor=right,
                        relation=None,
                        original_relation="UNLABELED",
                        category=category,
                        context_radius=context_radius,
                    )
                )
                if max_tasks > 0 and len(tasks) >= max_tasks:
                    break
            if max_tasks > 0 and len(tasks) >= max_tasks:
                break
        if max_tasks > 0 and len(tasks) >= max_tasks:
            break

    stats["num_tasks"] = len(tasks)
    return tasks, stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert MAVEN-ERE temporal data into canonical pairwise tasks."
    )
    parser.add_argument("--input", required=True, help="Input MAVEN-ERE JSONL file.")
    parser.add_argument(
        "--split",
        required=True,
        choices=["train", "valid", "test"],
        help="Dataset split represented by the input file.",
    )
    parser.add_argument("--output", required=True, help="Output canonical JSONL path.")
    parser.add_argument(
        "--stats-out", default="", help="Optional JSON path for conversion statistics."
    )
    parser.add_argument(
        "--category",
        default="maven_ere_temporal",
        help="Category label to assign to converted tasks.",
    )
    parser.add_argument(
        "--context-radius",
        type=int,
        default=1,
        help="Extra sentence radius to include around the anchor mention span.",
    )
    parser.add_argument(
        "--coarsen-overlap",
        action="store_true",
        help="Map MAVEN-ERE OVERLAP to SIMULTANEOUS instead of skipping it.",
    )
    parser.add_argument(
        "--no-event-event-only",
        action="store_true",
        help="Include EVENT-TIMEX and TIMEX-TIMEX pairs (default: EVENT-EVENT only).",
    )
    parser.add_argument(
        "--before-multiplier",
        type=float,
        default=2.0,
        help=(
            "BEFORE pool is capped at this multiple of the SIMULTANEOUS pool size. "
            "E.g. 2.0 → BEFORE:SIMULTANEOUS ≈ 2:1. "
            "Use a large value (e.g. 999) to keep all BEFORE pairs. "
            "Default: 2.0"
        ),
    )
    parser.add_argument(
        "--include-timex",
        action="store_true",
        help="Include TIMEX candidates when generating unlabeled test pairs.",
    )
    parser.add_argument(
        "--test-sentence-window",
        type=int,
        default=-1,
        help="For test conversion only: keep candidate pairs within this sentence distance. Use -1 for all pairs.",
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=0,
        help="Hard cap on output tasks applied after stratified sampling.",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for stratified sampling."
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if args.split == "test":
        tasks, stats = convert_maven_ere_test_candidates(
            input_path,
            split=args.split,
            category=args.category,
            context_radius=args.context_radius,
            include_timex=args.include_timex,
            sentence_window=args.test_sentence_window,
            max_docs=0,
            max_tasks=args.max_tasks,
        )
    else:
        tasks, stats = convert_maven_ere_temporal_split(
            input_path,
            split=args.split,
            category=args.category,
            context_radius=args.context_radius,
            coarsen_overlap=args.coarsen_overlap,
            event_event_only=not args.no_event_event_only,
            before_multiplier=args.before_multiplier,
            max_tasks=args.max_tasks,
            seed=args.seed,
        )

    _write_jsonl(Path(args.output), tasks)
    if args.stats_out:
        Path(args.stats_out).write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(f"Converted {len(tasks)} MAVEN-ERE tasks -> {args.output}")


if __name__ == "__main__":
    main()
