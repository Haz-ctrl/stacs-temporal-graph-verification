from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple

from src.constraints import default_verifier
from src.dataset import load_jsonl, parse_temporal_task
from src.dataset_validation import ValidationReport, validate_tasks
from src.evaluation import aggregate_prf, closure_prf, direct_edge_prf
from src.ollama_client import OllamaClient
from src.schemas import ParsedPrediction, ReasoningStep, TemporalTask
from src.structured_predictor import StructuredOllamaPredictor
from src.taxonomy import map_violation_to_category
from src.temporal_graph import Edge, EdgeLike, TemporalGraph, _to_edge

PredSource = Literal["llm", "gold", "empty", "noisy"]


@dataclass(frozen=True)
class BaselineRunConfig:
    data_path: str | Path
    model: str = "deepseek-r1:7b"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.0
    seed: int = 42
    max_tasks: int = 0
    pred_source: PredSource = "llm"
    log_raw: bool = False
    validate_data: bool = True
    strict_data: bool = False
    output_root: str | Path = Path("outputs") / "runs"


@dataclass(frozen=True)
class BaselineRunResult:
    run_id: str
    run_dir: Path
    predictions_path: Path
    report_path: Path
    report: Dict[str, Any]


def edges_to_jsonl(edges: Iterable[EdgeLike]) -> List[List[str]]:
    """Convert canonical edge-like triples into JSON-friendly list triples."""
    return [[a, b, r] for (a, b, r) in (_to_edge(edge) for edge in edges)]


def utc_stamp() -> str:
    """UTC timestamp suitable for folder names."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%SUTC")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def make_noisy_preds(
    *,
    allowed_events: List[str],
    gold_edges: List[Edge],
    seed: int,
) -> List[Edge]:
    """
    Deterministically generate noisy predictions to trigger constraints.
    """
    rng = random.Random(seed)
    pred: List[Edge] = list(gold_edges)

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

    if gold_edges:
        a, b, r = gold_edges[0]
        pred.append((b, a, r))

    if len(allowed_events) >= 3:
        a, b, c = allowed_events[0], allowed_events[1], allowed_events[2]
        pred.append((a, b, "BEFORE"))
        pred.append((b, c, "BEFORE"))
        pred.append((c, a, "BEFORE"))

    seen: set[Edge] = set()
    deduped: List[Edge] = []
    for edge in pred:
        if edge not in seen:
            seen.add(edge)
            deduped.append(edge)

    return deduped


def _prediction_from_source(
    *,
    task: TemporalTask,
    pred_source: PredSource,
    predictor: Optional[StructuredOllamaPredictor],
    seed: int,
) -> tuple[List[str], List[Edge], List[ReasoningStep], str, Optional[str]]:
    """
    Return:
      pred_events, pred_edges, reasoning_steps, answer, raw_output
    """
    if pred_source == "llm":
        if predictor is None:
            raise ValueError("Structured predictor is required when pred_source='llm'.")
        parsed: ParsedPrediction = predictor.predict(task)
        return (
            list(parsed.pred_events),
            list(parsed.pred_edges),
            list(parsed.reasoning_steps),
            parsed.answer,
            parsed.raw_output,
        )

    if pred_source == "gold":
        return (list(task.events), list(task.gold_relations), [], "", None)

    if pred_source == "empty":
        return (list(task.events), [], [], "", None)

    pred_edges = make_noisy_preds(
        allowed_events=list(task.events),
        gold_edges=list(task.gold_relations),
        seed=seed,
    )
    return (list(task.events), pred_edges, [], "", None)


def run_baseline(config: BaselineRunConfig) -> BaselineRunResult:
    raw_tasks: List[Dict[str, Any]] = load_jsonl(config.data_path)
    if config.max_tasks > 0:
        raw_tasks = raw_tasks[: config.max_tasks]

    if config.validate_data:
        validation_report: ValidationReport = validate_tasks(
            raw_tasks,
            strict=config.strict_data,
            require_expected_fields=False,
        )
        if validation_report.num_errors > 0:
            print(
                f"❌ Dataset validation failed: "
                f"errors={validation_report.num_errors} warnings={validation_report.num_warnings}"
            )
            for issue in validation_report.issues[:20]:
                if issue.severity == "error":
                    print(f"- [error] {issue.task_id} {issue.code}: {issue.message}")
            raise SystemExit(1)
        print(f"✅ Dataset validation passed: errors=0 warnings={validation_report.num_warnings}")

    tasks: List[TemporalTask] = [parse_temporal_task(obj) for obj in raw_tasks]

    run_id = utc_stamp()
    output_root = Path(config.output_root)
    run_dir = output_root / run_id
    ensure_dir(run_dir)

    valid_count = 0
    invalid_count = 0
    violation_counts: Dict[str, int] = {}
    taxonomy_counts: Dict[str, int] = {}

    expected_valid_tasks = 0
    expected_invalid_tasks = 0

    overcommit_task_count = 0
    overcommit_edge_count = 0
    overcommit_hit_count = 0

    direct_correct_total = 0
    direct_pred_total = 0
    direct_gold_total = 0

    closure_correct_total = 0
    closure_pred_total = 0
    closure_gold_total = 0

    client: Optional[OllamaClient] = None
    predictor: Optional[StructuredOllamaPredictor] = None
    if config.pred_source == "llm":
        client = OllamaClient(base_url=config.base_url)
        predictor = StructuredOllamaPredictor(
            model=config.model,
            client=client,
            temperature=config.temperature,
            seed=config.seed,
        )

    verifier = default_verifier()

    config_snapshot: Dict[str, Any] = {
        "run_id": run_id,
        "data_path": str(Path(config.data_path)),
        "num_tasks": len(tasks),
        "pred_source": config.pred_source,
        "model": config.model,
        "base_url": config.base_url,
        "temperature": config.temperature,
        "seed": config.seed,
        "log_raw": config.log_raw,
        "validate_data": config.validate_data,
        "strict_data": config.strict_data,
    }
    write_json(run_dir / "config.json", config_snapshot)

    preds_path = run_dir / "predictions.jsonl"
    failures: List[Dict[str, Any]] = []

    with preds_path.open("w", encoding="utf-8") as handle:
        for idx, task in enumerate(tasks, start=1):
            try:
                if task.expected_valid:
                    expected_valid_tasks += 1
                else:
                    expected_invalid_tasks += 1

                pred_events, pred_edges, reasoning_steps, answer, raw_output = _prediction_from_source(
                    task=task,
                    pred_source=config.pred_source,
                    predictor=predictor,
                    seed=config.seed + idx,
                )

                if len(task.gold_relations) == 0:
                    overcommit_task_count += 1
                    overcommit_edge_count += len(pred_edges)
                    if len(pred_edges) > 0:
                        overcommit_hit_count += 1

                tg = TemporalGraph()
                tg.add_events(task.events)
                tg.add_events(pred_events)
                tg.add_edges(pred_edges)

                violations = verifier.verify(
                    tg,
                    allowed_events=task.events,
                    gold_relations=task.gold_relations,
                    pred_edges=pred_edges,
                    reasoning_steps=reasoning_steps,
                )
                is_valid = len(violations) == 0

                if is_valid:
                    valid_count += 1
                else:
                    invalid_count += 1

                task_taxonomy_categories: List[str] = []
                for violation in violations:
                    violation_counts[violation.type] = violation_counts.get(violation.type, 0) + 1
                    category = map_violation_to_category(violation.type)
                    taxonomy_counts[category] = taxonomy_counts.get(category, 0) + 1
                    task_taxonomy_categories.append(category)

                task_taxonomy_categories = sorted(set(task_taxonomy_categories))

                task_direct_metrics: Optional[Dict[str, Any]] = None
                task_closure_metrics: Optional[Dict[str, Any]] = None

                if task.expected_valid and len(task.gold_relations) > 0:
                    direct_result = direct_edge_prf(task.gold_relations, pred_edges)
                    closure_result = closure_prf(task.events, task.gold_relations, pred_edges)

                    direct_correct_total += direct_result.correct
                    direct_pred_total += direct_result.pred_total
                    direct_gold_total += direct_result.gold_total

                    closure_correct_total += closure_result.correct
                    closure_pred_total += closure_result.pred_total
                    closure_gold_total += closure_result.gold_total

                    task_direct_metrics = asdict(direct_result)
                    task_closure_metrics = asdict(closure_result)

                record: Dict[str, Any] = {
                    "id": task.id,
                    "category": task.category,
                    "expected_valid": task.expected_valid,
                    "expected_consistent": task.expected_consistent,
                    "question": task.question,
                    "events": list(task.events),
                    "gold_relations": edges_to_jsonl(task.gold_relations),
                    "pred_events": list(pred_events),
                    "pred_edges": edges_to_jsonl(pred_edges),
                    "answer": answer,
                    "reasoning_steps": [asdict(step) for step in reasoning_steps],
                    "graph": {
                        "num_nodes": len(tg.nodes()),
                        "num_edges": len(tg.edges()),
                    },
                    "is_valid": is_valid,
                    "violations": [asdict(violation) for violation in violations],
                    "taxonomy_categories": task_taxonomy_categories,
                }

                if task_direct_metrics is not None:
                    record["direct_metrics"] = task_direct_metrics
                if task_closure_metrics is not None:
                    record["closure_metrics"] = task_closure_metrics

                if config.log_raw and raw_output is not None:
                    record["raw_output"] = raw_output

                handle.write(json.dumps(record) + "\n")
                print(
                    f"[{task.id}] pred_source={config.pred_source} edges={len(pred_edges)} "
                    f"valid={is_valid} violations={len(violations)}"
                )

            except Exception as exc:
                failures.append({"id": task.id, "error": repr(exc)})
                print(f"[{task.id}] ERROR: {exc!r}")

    direct_summary = asdict(aggregate_prf(direct_correct_total, direct_pred_total, direct_gold_total))
    closure_summary = asdict(aggregate_prf(closure_correct_total, closure_pred_total, closure_gold_total))

    report: Dict[str, Any] = {
        "run_id": run_id,
        "num_tasks": len(tasks),
        "num_failures": len(failures),
        "failures": failures,
        "predictions_file": str(preds_path),
        "pred_source": config.pred_source,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "validity_rate": (valid_count / len(tasks)) if tasks else 0.0,
        "violation_counts": violation_counts,
        "taxonomy_counts": taxonomy_counts,
        "dataset": {
            "expected_valid_tasks": expected_valid_tasks,
            "expected_invalid_tasks": expected_invalid_tasks,
        },
        "overcommitment": {
            "num_gold_empty_tasks": overcommit_task_count,
            "num_overcommit_tasks": overcommit_hit_count,
            "num_overcommit_edges": overcommit_edge_count,
            "task_overcommit_rate": (overcommit_hit_count / overcommit_task_count) if overcommit_task_count else 0.0,
            "avg_overcommit_edges_per_gold_empty_task": (
                overcommit_edge_count / overcommit_task_count
            ) if overcommit_task_count else 0.0,
        },
        "metrics_expected_valid_only": {
            "direct": direct_summary,
            "closure": closure_summary,
        },
    }

    report_path = run_dir / "report.json"
    write_json(report_path, report)

    print(f"\n✅ Run saved to: {run_dir}")
    if failures:
        print(f"⚠️  Some tasks failed ({len(failures)}). See report.json for details.")

    return BaselineRunResult(
        run_id=run_id,
        run_dir=run_dir,
        predictions_path=preds_path,
        report_path=report_path,
        report=report,
    )


def parse_args() -> BaselineRunConfig:
    ap = argparse.ArgumentParser(description="Run temporal graph baseline and save reproducible outputs.")
    ap.add_argument("--data", default="data/sample_tasks.jsonl", help="Path to JSONL dataset.")
    ap.add_argument("--model", default="deepseek-r1:7b", help="Ollama model tag.")
    ap.add_argument("--base-url", default="http://localhost:11434", help="Ollama server base URL.")
    ap.add_argument("--temperature", type=float, default=0.0, help="Decoding temperature.")
    ap.add_argument("--seed", type=int, default=42, help="Random seed.")
    ap.add_argument("--max-tasks", type=int, default=0, help="Limit tasks for quick tests (0 = all).")
    ap.add_argument(
        "--pred-source",
        choices=["llm", "gold", "empty", "noisy"],
        default="llm",
        help="Where to source predictions.",
    )
    ap.add_argument("--log-raw", action="store_true", help="Log raw model output in predictions.jsonl.")
    ap.add_argument("--validate-data", action="store_true", help="Validate dataset before running.")
    ap.add_argument("--strict-data", action="store_true", help="Use stricter dataset validation.")
    ap.set_defaults(validate_data=True)
    args = ap.parse_args()

    return BaselineRunConfig(
        data_path=args.data,
        model=args.model,
        base_url=args.base_url,
        temperature=args.temperature,
        seed=args.seed,
        max_tasks=args.max_tasks,
        pred_source=args.pred_source,
        log_raw=args.log_raw,
        validate_data=args.validate_data,
        strict_data=args.strict_data,
    )


def main() -> None:
    config = parse_args()
    run_baseline(config)


if __name__ == "__main__":
    main()