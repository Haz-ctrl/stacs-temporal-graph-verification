from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

# Make `src` importable when this script is invoked directly from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.constraints import default_verifier
from src.results import VerificationResult
from src.schemas import Edge, ReasoningStep
from src.temporal_graph import TemporalGraph, _to_edge


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def _reasoning_step_from_json(obj: Any) -> ReasoningStep:
    if isinstance(obj, ReasoningStep):
        return obj
    if not isinstance(obj, dict):
        raise ValueError(f"Invalid reasoning step: {obj!r}")
    return ReasoningStep(
        step_id=int(obj.get("step_id", 0)),
        text=str(obj.get("text", "")),
        supports=[_to_edge(edge) for edge in obj.get("supports", [])],
        confidence=obj.get("confidence"),
    )


def _verification_to_json(
    verifier: Any,
    verification: VerificationResult,
    *,
    pred_edges: tuple[Edge, ...],
    reasoning_steps: tuple[ReasoningStep, ...],
) -> Dict[str, Any]:
    task_specific_formulas = verifier._task_specific_formulas(pred_edges, reasoning_steps)
    return {
        "specification_name": verifier.specification.name,
        "is_valid": verification.is_valid,
        "graph_valid": verification.graph_valid,
        "trace_grounded": verification.trace_grounded,
        "violations": [asdict(violation) for violation in verification.violations],
        "ltl_passed": len(verification.formula_violations) == 0,
        "formula_violations": [asdict(violation) for violation in verification.formula_violations],
        "violation_counts": verification.violation_counts,
        "formula_violation_counts": verification.formula_violation_counts,
        "layer_counts": verification.layer_counts,
        "first_violation_step": verification.first_violation_step,
        "spec_sources": verification.spec_sources,
        "active_specification": {
            "invariants": [invariant.name for invariant in verifier.specification.invariants],
            "formulas": [
                formula.serialise()
                for formula in [*verifier.specification.formulas, *task_specific_formulas]
            ],
        },
    }


def _is_parse_failure(record: Dict[str, Any]) -> bool:
    if record.get("parsed") is False:
        return True
    if "pred_edges" not in record:
        return True
    if "reasoning_steps" not in record:
        return True
    return False


def rescore_predictions(predictions_path: Path, output_path: Path) -> tuple[int, int, int]:
    verifier = default_verifier()
    records = _read_jsonl(predictions_path)
    rescored_records: List[Dict[str, Any]] = []
    rescored_count = 0
    parse_failures_skipped = 0
    verification_changes = 0

    for record in records:
        if _is_parse_failure(record):
            parse_failures_skipped += 1
            rescored_records.append(record)
            continue

        pred_edges = tuple(_to_edge(edge) for edge in record.get("pred_edges", []))
        reasoning_steps = tuple(
            _reasoning_step_from_json(step)
            for step in record.get("reasoning_steps", [])
        )
        allowed_events = list(record.get("events", []))
        pred_events = list(record.get("pred_events", []))

        graph = TemporalGraph()
        graph.add_events(allowed_events)
        graph.add_events(pred_events)
        graph.add_edges(pred_edges)

        old_valid = record.get("verification", {}).get("is_valid")
        verification = verifier.verify(
            graph,
            allowed_events=allowed_events,
            pred_edges=pred_edges,
            reasoning_steps=reasoning_steps,
        )

        updated = dict(record)
        updated["verification"] = _verification_to_json(
            verifier,
            verification,
            pred_edges=pred_edges,
            reasoning_steps=reasoning_steps,
        )
        rescored_records.append(updated)
        rescored_count += 1

        if old_valid is not None and bool(old_valid) != verification.is_valid:
            verification_changes += 1

    _write_jsonl(output_path, rescored_records)
    return rescored_count, parse_failures_skipped, verification_changes


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-run current verifier on an existing predictions.jsonl.")
    parser.add_argument("--predictions", required=True, help="Path to predictions.jsonl.")
    parser.add_argument(
        "--output",
        default="",
        help="Output path. Defaults to predictions_rescored.jsonl beside --predictions.",
    )
    args = parser.parse_args()

    predictions_path = Path(args.predictions)
    output_path = Path(args.output) if args.output else predictions_path.with_name("predictions_rescored.jsonl")
    rescored, skipped, changed = rescore_predictions(predictions_path, output_path)
    print(f"Records rescored: {rescored}")
    print(f"Parse failures skipped: {skipped}")
    print(f"Verification changes: {changed}")
    print(f"Wrote: {output_path}")


if __name__ == "__main__":
    main()
