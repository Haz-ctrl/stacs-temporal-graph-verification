"""Convert MATRES temporal relations into canonical pairwise tasks.

MATRES labels start-point temporal relations between verb events.  The current
verifier supports the coarse label set used here:

    BEFORE -> BEFORE
    AFTER  -> AFTER
    EQUAL  -> SIMULTANEOUS
    VAGUE  -> UNKNOWN

UNKNOWN/VAGUE tasks are kept as direct pairwise classification examples.  They
do not contribute ordering edges and should therefore be analysed through
direct/pairwise label metrics and abstention behaviour, not closure F1.
"""
from __future__ import annotations

import argparse
import json
import random
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


MATRES_LABEL_MAP: Dict[str, str] = {
    "BEFORE": "BEFORE",
    "AFTER": "AFTER",
    "EQUAL": "SIMULTANEOUS",
    "VAGUE": "UNKNOWN",
}


@dataclass(frozen=True)
class MatresRelation:
    doc_id: str
    verb1: str
    verb2: str
    eiid1: str
    eiid2: str
    original_relation: str
    mapped_relation: str
    source_name: str
    row_index: int


@dataclass(frozen=True)
class EventMention:
    eid: str
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class EventInstance:
    eiid: str
    eid: str
    tense: str
    aspect: str
    polarity: str
    pos: str


@dataclass(frozen=True)
class TimeMLDocument:
    doc_id: str
    title: str
    text: str
    paragraph_spans: List[Tuple[int, int]]
    events_by_eid: Dict[str, EventMention]
    instances_by_eiid: Dict[str, EventInstance]


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def _read_text(path_or_url: str) -> str:
    if path_or_url.startswith(("http://", "https://")):
        with urllib.request.urlopen(path_or_url) as response:
            return response.read().decode("utf-8")
    return Path(path_or_url).read_text(encoding="utf-8")


def _normalise_eiid(value: str) -> str:
    raw = str(value).strip()
    if not raw:
        raise ValueError("MATRES eiid must be non-empty.")
    return raw if raw.lower().startswith("ei") else f"ei{raw}"


def map_matres_relation(relation: str) -> Optional[str]:
    return MATRES_LABEL_MAP.get(str(relation).strip().upper())


def load_matres_relations(inputs: Sequence[str]) -> Tuple[List[MatresRelation], Dict[str, Any]]:
    relations: List[MatresRelation] = []
    skipped = Counter()
    raw_counts = Counter()
    mapped_counts = Counter()

    for source in inputs:
        text = _read_text(source)
        source_name = Path(source).name or source
        for row_index, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) != 6:
                parts = line.split()
            if len(parts) != 6:
                skipped["malformed_row"] += 1
                continue

            doc_id, verb1, verb2, eiid1, eiid2, raw_relation = [part.strip() for part in parts]
            raw_relation = raw_relation.upper()
            raw_counts[raw_relation] += 1
            mapped = map_matres_relation(raw_relation)
            if mapped is None:
                skipped[f"unmapped:{raw_relation}"] += 1
                continue

            relations.append(
                MatresRelation(
                    doc_id=doc_id,
                    verb1=verb1,
                    verb2=verb2,
                    eiid1=_normalise_eiid(eiid1),
                    eiid2=_normalise_eiid(eiid2),
                    original_relation=raw_relation,
                    mapped_relation=mapped,
                    source_name=source_name,
                    row_index=row_index,
                )
            )
            mapped_counts[mapped] += 1

    return relations, {
        "input_sources": list(inputs),
        "raw_relation_counts": dict(sorted(raw_counts.items())),
        "mapped_relation_counts": dict(sorted(mapped_counts.items())),
        "skipped_relation_counts": dict(sorted(skipped.items())),
    }


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _append_text_with_event_offsets(
    node: ET.Element,
    chunks: List[str],
    events_by_eid: Dict[str, EventMention],
) -> None:
    if node.text:
        chunks.append(node.text)

    for child in list(node):
        if _local_name(child.tag) == "EVENT":
            start = sum(len(chunk) for chunk in chunks)
            event_text = "".join(child.itertext())
            chunks.append(event_text)
            end = sum(len(chunk) for chunk in chunks)
            eid = child.attrib.get("eid")
            if eid:
                events_by_eid[eid] = EventMention(
                    eid=eid,
                    text=event_text.strip(),
                    start=start,
                    end=end,
                )
        else:
            _append_text_with_event_offsets(child, chunks, events_by_eid)

        if child.tail:
            chunks.append(child.tail)


def _paragraph_spans(text: str) -> List[Tuple[int, int]]:
    spans: List[Tuple[int, int]] = []
    cursor = 0
    for raw_line in text.splitlines(keepends=True):
        line_start = cursor
        line_end = cursor + len(raw_line)
        stripped = raw_line.strip()
        if stripped:
            leading = len(raw_line) - len(raw_line.lstrip())
            trailing = len(raw_line.rstrip()) - len(stripped)
            spans.append((line_start + leading, max(line_start + leading, line_end - trailing)))
        cursor = line_end
    return spans or [(0, len(text))]


def parse_timeml_document(path: Path) -> TimeMLDocument:
    root = ET.parse(path).getroot()
    doc_id = (root.findtext("DOCID") or path.name.split(".tml", 1)[0]).strip()
    title = (root.findtext("TITLE") or "").strip()
    text_node = root.find("TEXT")
    if text_node is None:
        raise ValueError(f"{path} is missing a TEXT node.")

    chunks: List[str] = []
    events_by_eid: Dict[str, EventMention] = {}
    _append_text_with_event_offsets(text_node, chunks, events_by_eid)
    text = "".join(chunks)

    instances_by_eiid: Dict[str, EventInstance] = {}
    for node in root.iter():
        if _local_name(node.tag) != "MAKEINSTANCE":
            continue
        eiid = node.attrib.get("eiid")
        eid = node.attrib.get("eventID") or node.attrib.get("eid")
        if not eiid or not eid:
            continue
        instances_by_eiid[eiid] = EventInstance(
            eiid=eiid,
            eid=eid,
            tense=node.attrib.get("tense", ""),
            aspect=node.attrib.get("aspect", ""),
            polarity=node.attrib.get("polarity", ""),
            pos=node.attrib.get("pos", ""),
        )

    return TimeMLDocument(
        doc_id=doc_id,
        title=title,
        text=text,
        paragraph_spans=_paragraph_spans(text),
        events_by_eid=events_by_eid,
        instances_by_eiid=instances_by_eiid,
    )


def load_timeml_documents(root: Path) -> Dict[str, TimeMLDocument]:
    if not root.is_dir():
        raise ValueError(f"TimeML root directory not found: {root}")

    documents: Dict[str, TimeMLDocument] = {}
    for path in sorted(root.rglob("*.tml")):
        doc = parse_timeml_document(path)
        documents[doc.doc_id] = doc
    return documents


def _paragraph_index_for_offset(spans: Sequence[Tuple[int, int]], offset: int) -> int:
    for index, (start, end) in enumerate(spans):
        if start <= offset <= end:
            return index
    return 0


def _passage_for_events(
    doc: TimeMLDocument,
    left: EventMention,
    right: EventMention,
    *,
    context_radius: int,
) -> Tuple[str, int, int]:
    left_index = _paragraph_index_for_offset(doc.paragraph_spans, left.start)
    right_index = _paragraph_index_for_offset(doc.paragraph_spans, right.start)
    start_index = max(0, min(left_index, right_index) - context_radius)
    end_index = min(len(doc.paragraph_spans) - 1, max(left_index, right_index) + context_radius)

    start_offset = doc.paragraph_spans[start_index][0]
    end_offset = doc.paragraph_spans[end_index][1]
    passage = " ".join(doc.text[start_offset:end_offset].split())
    return passage, start_index, end_index


def _label_for_event(event: EventMention, eiid: str, fallback_verb: str) -> str:
    surface = event.text.strip() or fallback_verb.strip() or eiid
    return f"{surface} [{eiid}]"


def _prompt_for_pair(*, title: str, passage: str, left_label: str, right_label: str) -> str:
    lines: List[str] = []
    if title:
        lines.extend(["Title:", title, ""])
    lines.extend(
        [
            "Passage:",
            passage,
            "",
            "Determine the temporal relation between the following event mentions.",
            f"- {left_label}",
            f"- {right_label}",
            "",
            "Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN.",
        ]
    )
    return "\n".join(lines)


def build_matres_tasks(
    relations: Sequence[MatresRelation],
    documents: Dict[str, TimeMLDocument],
    *,
    category: str,
    context_radius: int,
    max_per_label: int,
    max_tasks: int,
    seed: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    pools: Dict[str, List[MatresRelation]] = {label: [] for label in MATRES_LABEL_MAP.values()}
    skipped = Counter()

    for relation in relations:
        doc = documents.get(relation.doc_id)
        if doc is None:
            skipped["missing_document"] += 1
            continue
        left_instance = doc.instances_by_eiid.get(relation.eiid1)
        right_instance = doc.instances_by_eiid.get(relation.eiid2)
        if left_instance is None or right_instance is None:
            skipped["missing_instance"] += 1
            continue
        if left_instance.eid not in doc.events_by_eid or right_instance.eid not in doc.events_by_eid:
            skipped["missing_event_mention"] += 1
            continue
        pools[relation.mapped_relation].append(relation)

    rng = random.Random(seed)
    sampled: List[MatresRelation] = []
    pool_sizes = {label: len(rows) for label, rows in sorted(pools.items())}
    sampled_counts: Counter[str] = Counter()

    for label in sorted(pools):
        rows = list(pools[label])
        rng.shuffle(rows)
        if max_per_label > 0:
            rows = rows[:max_per_label]
        sampled.extend(rows)
        sampled_counts[label] += len(rows)

    rng.shuffle(sampled)
    if max_tasks > 0:
        sampled = sampled[:max_tasks]
        sampled_counts = Counter(row.mapped_relation for row in sampled)

    tasks: List[Dict[str, Any]] = []
    for index, relation in enumerate(sampled):
        doc = documents[relation.doc_id]
        left_instance = doc.instances_by_eiid[relation.eiid1]
        right_instance = doc.instances_by_eiid[relation.eiid2]
        left_event = doc.events_by_eid[left_instance.eid]
        right_event = doc.events_by_eid[right_instance.eid]
        left_label = _label_for_event(left_event, relation.eiid1, relation.verb1)
        right_label = _label_for_event(right_event, relation.eiid2, relation.verb2)
        passage, paragraph_start, paragraph_end = _passage_for_events(
            doc,
            left_event,
            right_event,
            context_radius=context_radius,
        )

        task_id = f"matres_{relation.source_name.removesuffix('.txt')}_{relation.doc_id}_{relation.row_index:06d}"
        tasks.append(
            {
                "id": task_id,
                "category": category,
                "question": _prompt_for_pair(
                    title=doc.title,
                    passage=passage,
                    left_label=left_label,
                    right_label=right_label,
                ),
                "events": [left_label, right_label],
                "gold_relations": [[left_label, right_label, relation.mapped_relation]],
                "expected_valid": True,
                "expected_consistent": True,
                "metadata": {
                    "source_format": "matres",
                    "document_id": doc.doc_id,
                    "source_file": relation.source_name,
                    "row_index": relation.row_index,
                    "original_relation": relation.original_relation,
                    "mapped_relation": relation.mapped_relation,
                    "source_verb": relation.verb1,
                    "target_verb": relation.verb2,
                    "source_eiid": relation.eiid1,
                    "target_eiid": relation.eiid2,
                    "source_eid": left_instance.eid,
                    "target_eid": right_instance.eid,
                    "source_event_text": left_event.text,
                    "target_event_text": right_event.text,
                    "source_pos": left_instance.pos,
                    "target_pos": right_instance.pos,
                    "paragraph_start": paragraph_start,
                    "paragraph_end": paragraph_end,
                },
            }
        )

    stats = {
        "num_documents": len(documents),
        "num_tasks": len(tasks),
        "category": category,
        "context_radius": context_radius,
        "max_per_label": max_per_label,
        "max_tasks": max_tasks,
        "seed": seed,
        "pool_sizes": pool_sizes,
        "sampled_counts": dict(sorted(sampled_counts.items())),
        "skipped_counts": dict(sorted(skipped.items())),
        "analysis_note": (
            "UNKNOWN labels originate from MATRES VAGUE. Report these through "
            "direct/pairwise label metrics and abstention behaviour; UNKNOWN "
            "does not contribute to ordering closure."
        ),
    }
    return tasks, stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert MATRES relations into canonical pairwise JSONL tasks.")
    parser.add_argument(
        "--matres-input",
        action="append",
        required=True,
        help="MATRES relation file path or URL. Repeat for multiple files.",
    )
    parser.add_argument(
        "--timeml-root",
        required=True,
        help="Directory containing TimeML .tml files referenced by the MATRES rows.",
    )
    parser.add_argument("--output", required=True, help="Output canonical JSONL path.")
    parser.add_argument("--stats-out", default="", help="Optional JSON path for conversion statistics.")
    parser.add_argument("--category", default="matres_temporal", help="Category label to assign to converted tasks.")
    parser.add_argument(
        "--context-radius",
        type=int,
        default=0,
        help="Extra paragraph radius to include around the event pair.",
    )
    parser.add_argument(
        "--max-per-label",
        type=int,
        default=100,
        help="Maximum sampled tasks per canonical label. Use 0 to keep all available rows.",
    )
    parser.add_argument(
        "--max-tasks",
        type=int,
        default=0,
        help="Optional hard cap applied after per-label sampling and shuffling.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for stratified sampling.")
    args = parser.parse_args()

    relations, relation_stats = load_matres_relations(args.matres_input)
    documents = load_timeml_documents(Path(args.timeml_root))
    tasks, task_stats = build_matres_tasks(
        relations,
        documents,
        category=args.category,
        context_radius=args.context_radius,
        max_per_label=args.max_per_label,
        max_tasks=args.max_tasks,
        seed=args.seed,
    )

    _write_jsonl(Path(args.output), tasks)
    if args.stats_out:
        stats = {**relation_stats, **task_stats}
        Path(args.stats_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.stats_out).write_text(json.dumps(stats, indent=2), encoding="utf-8")

    print(f"Converted {len(tasks)} MATRES tasks -> {args.output}")


if __name__ == "__main__":
    main()
