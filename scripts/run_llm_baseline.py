from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.dataset import load_jsonl
from src.temporal_graph import TemporalGraph
from src.constraints import default_verifier
from src.ollama_client import OllamaClient
from src.ollama_predictor import OllamaPredictor

def utc_stamp() -> str:
    """UTC timestamp suitable for folder names."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%SUTC")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Run Ollama over JSONL tasks and save reproducible outputs.")
    ap.add_argument("--data", default="data/sample_tasks.jsonl", help="Path to JSONL dataset.")
    ap.add_argument("--model", default="deepseek-r1:7b", help="Ollama model tag (see: ollama list).")
    ap.add_argument("--base-url", default="http://localhost:11434", help="Ollama server base URL.")
    ap.add_argument("--temperature", type=float, default=0.0, help="Decoding temperature (0.0 recommended).")
    ap.add_argument("--seed", type=int, default=42, help="Random seed (if backend supports it).")
    ap.add_argument("--max-tasks", type=int, default=0, help="Limit tasks for quick tests (0 = all).")
    args = ap.parse_args()

    # Load tasks
    tasks: List[Dict[str, Any]] = load_jsonl(args.data)
    if args.max_tasks and args.max_tasks > 0:
        tasks = tasks[: args.max_tasks]

    # Prepare run directory
    run_id = utc_stamp()
    run_dir = Path("outputs") / "runs" / run_id
    ensure_dir(run_dir)

    # TODO find a better place to put these counts
    valid_count = 0
    invalid_count = 0
    violation_counts = {}  # Dict[str, int]
    overcommit_task_count = 0      # number of tasks with empty gold_relations
    overcommit_edge_count = 0      # number of predicted edges on those tasks
    overcommit_hit_count = 0       # number of tasks where model predicted >=1 edge despite empty gold

    # Build predictor
    client = OllamaClient(base_url=args.base_url)
    predictor = OllamaPredictor(
        model=args.model,
        client=client,
        temperature=args.temperature,
        seed=args.seed,
    )
    verifier = default_verifier()

    # Save config snapshot for reproducibility
    config = {
        "run_id": run_id,
        "data_path": str(Path(args.data)),
        "num_tasks": len(tasks),
        "predictor": predictor.metadata() if hasattr(predictor, "metadata") else {
            "provider": "ollama",
            "base_url": args.base_url,
            "model": args.model,
            "temperature": args.temperature,
            "seed": args.seed,
        },
    }
    write_json(run_dir / "config.json", config)

    # Run predictions
    preds_path = run_dir / "predictions.jsonl"
    failures: List[Dict[str, Any]] = []

    with preds_path.open("w", encoding="utf-8") as f:
        for idx, task in enumerate(tasks, start=1):
            task_id = task.get("id", f"task_{idx:03d}")

            try:
                pred_edges = predictor.predict_edges(task)

                gold = task.get("gold_relations", [])
                if len(gold) == 0:
                    overcommit_task_count += 1
                    overcommit_edge_count += len(pred_edges)
                    if len(pred_edges) > 0:
                        overcommit_hit_count += 1

                # Build temporal graph from predicted edges
                tg = TemporalGraph()
                allowed_events = task.get("events", [])
                tg.add_events(allowed_events)
                tg.add_edges(pred_edges)

                # Compute violations
                violations = verifier.verify(tg, allowed_events=allowed_events)
                is_valid = (len(violations) == 0)

                if is_valid:
                    valid_count += 1
                else:
                    invalid_count += 1

                for v in violations:
                    violation_counts[v.type] = violation_counts.get(v.type, 0) + 1

                rec = {
                    "id": task_id,
                    "question": task.get("question", ""),
                    "events": allowed_events,
                    "gold_relations": task.get("gold_relations", []),
                    "pred_edges": pred_edges,

                    # New: graph + verification
                    "graph": {
                        "num_nodes": len(tg.nodes()),
                        "num_edges": len(tg.edges()),
                        # optional: include edges for debugging (you already store pred_edges)
                    },
                    "is_valid": is_valid,
                    "violations": [v.__dict__ for v in violations],
                }

                f.write(json.dumps(rec) + "\n")
                print(f"[{task_id}] edges={len(pred_edges)} valid={is_valid} violations={len(violations)}")

            except Exception as e:
                failures.append({"id": task_id, "error": repr(e)})
                print(f"[{task_id}] ERROR: {e!r}")

    # Save report summary
    report = {
        "run_id": run_id,
        "num_tasks": len(tasks),
        "num_failures": len(failures),
        "failures": failures,
        "predictions_file": str(preds_path),

        # Verification aggregates
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "validity_rate": (valid_count / len(tasks)) if tasks else 0.0,
        "violation_counts": violation_counts,
    }
    report["overcommitment"] = {
        "num_gold_empty_tasks": overcommit_task_count,
        "num_overcommit_tasks": overcommit_hit_count,
        "num_overcommit_edges": overcommit_edge_count,
        # two useful rates:
        "task_overcommit_rate": (overcommit_hit_count / overcommit_task_count) if overcommit_task_count else 0.0,
        "avg_overcommit_edges_per_gold_empty_task": (overcommit_edge_count / overcommit_task_count) if overcommit_task_count else 0.0,
    }
    write_json(run_dir / "report.json", report)

    print(f"\n✅ Run saved to: {run_dir}")
    if failures:
        print(f"⚠️  Some tasks failed ({len(failures)}). See report.json for details.")


if __name__ == "__main__":
    main()