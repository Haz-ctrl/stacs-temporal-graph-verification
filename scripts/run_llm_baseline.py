# scripts/run_llm_baseline.py
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.dataset import load_jsonl
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

    # Build predictor
    client = OllamaClient(base_url=args.base_url)
    predictor = OllamaPredictor(
        model=args.model,
        client=client,
        temperature=args.temperature,
        seed=args.seed,
    )

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
                rec = {
                    "id": task_id,
                    "question": task.get("question", ""),
                    "events": task.get("events", []),
                    "gold_relations": task.get("gold_relations", []),
                    "pred_edges": pred_edges,
                }
                f.write(json.dumps(rec) + "\n")
                print(f"[{task_id}] edges={len(pred_edges)}")
            except Exception as e:
                # Keep the run going and log failures
                failures.append({"id": task_id, "error": repr(e)})
                print(f"[{task_id}] ERROR: {e!r}")

    # Save report summary
    report = {
        "run_id": run_id,
        "num_tasks": len(tasks),
        "num_failures": len(failures),
        "failures": failures,
        "predictions_file": str(preds_path),
    }
    write_json(run_dir / "report.json", report)

    print(f"\n✅ Run saved to: {run_dir}")
    if failures:
        print(f"⚠️  Some tasks failed ({len(failures)}). See report.json for details.")


if __name__ == "__main__":
    main()