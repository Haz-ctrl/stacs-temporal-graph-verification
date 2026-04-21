from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from scripts.run_llm_baseline import BaselineRunConfig, run_baseline
from src.ollama_client import (
    DEFAULT_OLLAMA_MAX_RETRIES,
    DEFAULT_OLLAMA_RETRY_BACKOFF_S,
    DEFAULT_OLLAMA_TIMEOUT_S,
)


def _load_manifest(path: str | Path) -> List[Dict[str, Any]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Sweep manifest must be a JSON list.")
    return [dict(entry) for entry in raw]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a sequential Ollama-backed model sweep.")
    parser.add_argument("--manifest", required=True, help="Path to model sweep manifest JSON.")
    parser.add_argument("--data", default="data/temporal_reasoning_eval.jsonl", help="Dataset path.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--temperature", type=float, default=0.0, help="Decoding temperature.")
    parser.add_argument("--log-raw", action="store_true", help="Log raw outputs in run artefacts.")
    parser.add_argument("--max-tasks", type=int, default=0, help="Limit tasks per run (0 = full dataset).")
    parser.add_argument("--base-url", default="http://localhost:11434", help="Default Ollama base URL.")
    parser.add_argument(
        "--timeout-s",
        type=int,
        default=DEFAULT_OLLAMA_TIMEOUT_S,
        help="Ollama read timeout in seconds.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_OLLAMA_MAX_RETRIES,
        help="Maximum number of transport attempts for each Ollama request.",
    )
    parser.add_argument(
        "--retry-backoff-s",
        type=float,
        default=DEFAULT_OLLAMA_RETRY_BACKOFF_S,
        help="Base backoff in seconds between exponential transport retries.",
    )
    parser.add_argument(
        "--output-root",
        default="outputs/runs",
        help="Directory under which per-run artefacts will be created.",
    )
    args = parser.parse_args()

    manifest = _load_manifest(args.manifest)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    run_manifest: Dict[str, Dict[str, Any]] = {}
    sweep_index: List[Dict[str, Any]] = []

    for entry in manifest:
        model = str(entry["model"])
        result = run_baseline(
            BaselineRunConfig(
                data_path=args.data,
                model=model,
                base_url=str(entry.get("base_url", args.base_url)),
                temperature=args.temperature,
                seed=args.seed,
                max_tasks=args.max_tasks,
                pred_source="llm",
                log_raw=args.log_raw,
                timeout_s=args.timeout_s,
                max_retries=args.max_retries,
                retry_backoff_s=args.retry_backoff_s,
                output_root=output_root,
            )
        )
        meta = {
            "model_label": entry.get("label", model),
            "family": entry.get("family", ""),
            "size_bucket": entry.get("size", ""),
            "reasoning_tuned": entry.get("reasoning_tuned", ""),
            "group": entry.get("group", ""),
            "notes": entry.get("notes", ""),
        }
        run_manifest[result.run_id] = meta
        sweep_index.append(
            {
                "run_id": result.run_id,
                "run_dir": str(result.run_dir),
                "model": model,
                "label": meta["model_label"],
            }
        )

    (output_root / "run_manifest.json").write_text(
        json.dumps({"runs": run_manifest}, indent=2),
        encoding="utf-8",
    )
    (output_root / "sweep_index.json").write_text(
        json.dumps(
            {
                "data_path": args.data,
                "seed": args.seed,
                "temperature": args.temperature,
                "timeout_s": args.timeout_s,
                "max_retries": args.max_retries,
                "retry_backoff_s": args.retry_backoff_s,
                "max_tasks": args.max_tasks,
                "runs": sweep_index,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Completed {len(sweep_index)} runs -> {output_root}")


if __name__ == "__main__":
    main()
