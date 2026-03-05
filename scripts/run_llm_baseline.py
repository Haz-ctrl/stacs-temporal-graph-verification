from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from src.constraints import default_verifier
from src.dataset import load_jsonl
from src.dataset_validation import validate_tasks
from src.ollama_client import OllamaClient
from src.ollama_predictor import OllamaPredictor, PROMPT_TEMPLATE
from src.temporal_graph import Edge, EdgeLike, TemporalGraph, _to_edge


def edges_to_jsonl(edges: Iterable[EdgeLike]) -> List[List[str]]:
    """Convert canonical edge-like triples into JSON-friendly list triples."""
    return [[a, b, r] for (a, b, r) in (_to_edge(e) for e in edges)]


def edges_to_tuples(edges: Iterable[EdgeLike]) -> List[Edge]:
    """Convert edge-like triples into canonical Edge tuples."""
    return [_to_edge(e) for e in edges]


def utc_stamp() -> str:
    """UTC timestamp suitable for folder names."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%SUTC")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def prf(correct: int, pred_total: int, gold_total: int) -> Dict[str, float]:
    precision = (correct / pred_total) if pred_total else 0.0
    recall = (correct / gold_total) if gold_total else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def make_noisy_preds(
    *,
    allowed_events: List[str],
    gold_edges: List[Edge],
    seed: int,
) -> List[Edge]:
    """
    Deterministically generate "bad" predictions to trigger constraints.
    Returns canonical Edge tuples.
    """
    rng = random.Random(seed)
    pred: List[Edge] = list(gold_edges)

    # Spurious edge
    if len(allowed_events) >= 2:
        candidates: List[Tuple[str, str]] = []
        for i in range(len(allowed_events)):
            for j in range(len(allowed_events)):
                if i != j:
                    candidates.append((allowed_events[i], allowed_events[j]))

        gold_pairs = {(a, b) for (a, b, _) in gold_edges}
        spurious_candidates = [(a, b) for (a, b) in candidates if (a, b) not in gold_pairs]
        if spurious_candidates:
            a, b = rng.choice(spurious_candidates)
            pred.append((a, b, "BEFORE"))

    # Contradiction of first gold edge
    if gold_edges:
        a, b, r = gold_edges[0]
        pred.append((b, a, r))

    # 3-cycle
    if len(allowed_events) >= 3:
        a, b, c = allowed_events[0], allowed_events[1], allowed_events[2]
        pred.append((a, b, "BEFORE"))
        pred.append((b, c, "BEFORE"))
        pred.append((c, a, "BEFORE"))

    # De-duplicate while preserving order
    seen: set[Edge] = set()
    deduped: List[Edge] = []
    for e in pred:
        if e not in seen:
            seen.add(e)
            deduped.append(e)

    return deduped


def build_prompt(task: Dict[str, Any]) -> str:
    """
    Build the exact same prompt as OllamaPredictor.predict_edges()
    so raw logging reflects what was actually asked.
    """
    events_block = "\n".join([f"- {e}" for e in task["events"]])
    return PROMPT_TEMPLATE.format(question=task["question"], events_block=events_block)


def main() -> None:
    ap = argparse.ArgumentParser(description="Run Ollama over JSONL tasks and save reproducible outputs.")
    ap.add_argument("--data", default="data/sample_tasks.jsonl", help="Path to JSONL dataset.")
    ap.add_argument("--model", default="deepseek-r1:7b", help="Ollama model tag (see: ollama list).")
    ap.add_argument("--base-url", default="http://localhost:11434", help="Ollama server base URL.")
    ap.add_argument("--temperature", type=float, default=0.0, help="Decoding temperature (0.0 recommended).")
    ap.add_argument("--seed", type=int, default=42, help="Random seed (if backend supports it).")
    ap.add_argument("--max-tasks", type=int, default=0, help="Limit tasks for quick tests (0 = all).")
    ap.add_argument(
        "--pred-source",
        choices=["llm", "gold", "empty", "noisy"],
        default="llm",
        help="Where to source predictions: llm (default), gold, empty, noisy (forces violations).",
    )
    ap.add_argument(
        "--log-raw",
        action="store_true",
        help="Log raw LLM output in predictions.jsonl (debugging only).",
    )
    ap.add_argument(
        "--validate-data",
        action="store_true",
        help="Validate dataset before running (recommended).",
    )
    ap.add_argument(
        "--strict-data",
        action="store_true",
        help="Stricter dataset validation (may error on minor issues).",
    )
    ap.set_defaults(validate_data=True)
    args = ap.parse_args()

    # Load tasks
    tasks: List[Dict[str, Any]] = load_jsonl(args.data)
    if args.max_tasks and args.max_tasks > 0:
        tasks = tasks[: args.max_tasks]

    # Validate dataset (recommended gate)
    if args.validate_data:
        rep = validate_tasks(tasks, strict=args.strict_data, require_expected_fields=False)
        if rep.num_errors > 0:
            print(f"❌ Dataset validation failed: errors={rep.num_errors} warnings={rep.num_warnings}")
            for it in rep.issues[:20]:
                if it.severity == "error":
                    print(f"- [error] {it.task_id} {it.code}: {it.message}")
            raise SystemExit(1)
        print(f"✅ Dataset validation passed: errors=0 warnings={rep.num_warnings}")

    # Prepare run directory
    run_id = utc_stamp()
    run_dir = Path("outputs") / "runs" / run_id
    ensure_dir(run_dir)

    # Verification aggregates (all tasks)
    valid_count = 0
    invalid_count = 0
    violation_counts: Dict[str, int] = {}

    # Dataset annotation counts
    expected_valid_tasks = 0
    expected_invalid_tasks = 0

    # Overcommitment counters (metric over gold-empty tasks)
    overcommit_task_count = 0
    overcommit_edge_count = 0
    overcommit_hit_count = 0

    # Metrics computed ONLY over expected_valid tasks (and only where gold is non-empty)
    direct_gold_total = 0
    direct_pred_total = 0
    direct_correct = 0

    closure_gold_total = 0
    closure_pred_total = 0
    closure_correct = 0

    # Predictor setup
    client: Optional[OllamaClient] = None
    predictor: Optional[OllamaPredictor] = None
    if args.pred_source == "llm":
        client = OllamaClient(base_url=args.base_url)
        predictor = OllamaPredictor(
            model=args.model,
            client=client,
            temperature=args.temperature,
            seed=args.seed,
        )

    verifier = default_verifier()

    # Save config snapshot
    config: Dict[str, Any] = {
        "run_id": run_id,
        "data_path": str(Path(args.data)),
        "num_tasks": len(tasks),
        "pred_source": args.pred_source,
        "model": args.model,
        "base_url": args.base_url,
        "temperature": args.temperature,
        "seed": args.seed,
        "log_raw": args.log_raw,
        "validate_data": args.validate_data,
        "strict_data": args.strict_data,
    }
    write_json(run_dir / "config.json", config)

    # Run predictions
    preds_path = run_dir / "predictions.jsonl"
    failures: List[Dict[str, Any]] = []

    with preds_path.open("w", encoding="utf-8") as f:
        for idx, task in enumerate(tasks, start=1):
            task_id = str(task.get("id", f"task_{idx:03d}"))

            try:
                allowed_events: List[str] = list(task.get("events", []))

                gold_raw: List[List[str]] = list(task.get("gold_relations", []))
                gold_edges: List[Edge] = edges_to_tuples(gold_raw)

                # Expected fields (default to True if missing, for backwards compatibility)
                expected_valid = bool(task.get("expected_valid", True))
                expected_consistent = bool(task.get("expected_consistent", True))
                if expected_valid:
                    expected_valid_tasks += 1
                else:
                    expected_invalid_tasks += 1

                raw_output: Optional[str] = None

                # Select prediction source -> always produce List[Edge]
                if args.pred_source == "llm":
                    assert predictor is not None
                    pred_edges: List[Edge] = predictor.predict_edges(task)

                    # Optional raw logging (second call, but deterministic with temp=0 + seed)
                    if args.log_raw:
                        assert client is not None
                        prompt = build_prompt(task)
                        raw_output = client.generate(
                            args.model,
                            prompt,
                            temperature=args.temperature,
                            seed=args.seed,
                        )

                elif args.pred_source == "gold":
                    pred_edges = list(gold_edges)

                elif args.pred_source == "empty":
                    pred_edges = []

                else:  # noisy
                    pred_edges = make_noisy_preds(
                        allowed_events=allowed_events,
                        gold_edges=gold_edges,
                        seed=args.seed + idx,
                    )

                # Overcommitment counters (metric)
                if len(gold_edges) == 0:
                    overcommit_task_count += 1
                    overcommit_edge_count += len(pred_edges)
                    if len(pred_edges) > 0:
                        overcommit_hit_count += 1

                # Build predicted temporal graph
                tg = TemporalGraph()
                tg.add_events(allowed_events)
                tg.add_edges(pred_edges)

                # Compute violations (pass gold + pred for edge-based constraints)
                violations = verifier.verify(
                    tg,
                    allowed_events=allowed_events,
                    gold_relations=gold_edges,
                    pred_edges=pred_edges,
                )
                is_valid = (len(violations) == 0)

                if is_valid:
                    valid_count += 1
                else:
                    invalid_count += 1

                for v in violations:
                    violation_counts[v.type] = violation_counts.get(v.type, 0) + 1

                # Metrics: ONLY on expected_valid tasks AND gold-nonempty
                if expected_valid and len(gold_edges) > 0:
                    gold_set = set(gold_edges)
                    pred_set = set(pred_edges)

                    direct_gold_total += len(gold_set)
                    direct_pred_total += len(pred_set)
                    direct_correct += len(gold_set & pred_set)

                    gold_g = TemporalGraph()
                    gold_g.add_events(allowed_events)
                    gold_g.add_edges(gold_edges)

                    gold_cl = gold_g.transitive_closure_pairs()
                    pred_cl = tg.transitive_closure_pairs()

                    closure_gold_total += len(gold_cl)
                    closure_pred_total += len(pred_cl)
                    closure_correct += len(gold_cl & pred_cl)

                rec: Dict[str, Any] = {
                    "id": task_id,
                    "category": task.get("category", ""),
                    "expected_valid": expected_valid,
                    "expected_consistent": expected_consistent,
                    "question": task.get("question", ""),
                    "events": allowed_events,
                    "gold_relations": edges_to_jsonl(gold_edges),
                    "pred_edges": edges_to_jsonl(pred_edges),
                    "graph": {
                        "num_nodes": len(tg.nodes()),
                        "num_edges": len(tg.edges()),
                    },
                    "is_valid": is_valid,
                    "violations": [v.__dict__ for v in violations],
                }

                if args.log_raw and raw_output is not None:
                    rec["raw_output"] = raw_output

                f.write(json.dumps(rec) + "\n")
                print(
                    f"[{task_id}] pred_source={args.pred_source} edges={len(pred_edges)} "
                    f"valid={is_valid} violations={len(violations)}"
                )

            except Exception as e:
                failures.append({"id": task_id, "error": repr(e)})
                print(f"[{task_id}] ERROR: {e!r}")

    # Report summary
    report: Dict[str, Any] = {
        "run_id": run_id,
        "num_tasks": len(tasks),
        "num_failures": len(failures),
        "failures": failures,
        "predictions_file": str(preds_path),
        "pred_source": args.pred_source,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "validity_rate": (valid_count / len(tasks)) if tasks else 0.0,
        "violation_counts": violation_counts,
        "dataset": {
            "expected_valid_tasks": expected_valid_tasks,
            "expected_invalid_tasks": expected_invalid_tasks,
        },
        "overcommitment": {
            "num_gold_empty_tasks": overcommit_task_count,
            "num_overcommit_tasks": overcommit_hit_count,
            "num_overcommit_edges": overcommit_edge_count,
            "task_overcommit_rate": (overcommit_hit_count / overcommit_task_count) if overcommit_task_count else 0.0,
            "avg_overcommit_edges_per_gold_empty_task": (overcommit_edge_count / overcommit_task_count)
            if overcommit_task_count
            else 0.0,
        },
        "metrics_expected_valid_only": {
            "direct": {
                **prf(direct_correct, direct_pred_total, direct_gold_total),
                "correct": direct_correct,
                "pred_total": direct_pred_total,
                "gold_total": direct_gold_total,
            },
            "closure": {
                **prf(closure_correct, closure_pred_total, closure_gold_total),
                "correct": closure_correct,
                "pred_total": closure_pred_total,
                "gold_total": closure_gold_total,
            },
        },
    }

    write_json(run_dir / "report.json", report)

    print(f"\n✅ Run saved to: {run_dir}")
    if failures:
        print(f"⚠️  Some tasks failed ({len(failures)}). See report.json for details.")


if __name__ == "__main__":
    main()