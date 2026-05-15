from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from src.benchmark_adapters import convert_tempeval_style_record
from src.dataset import load_jsonl


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a simplified TempEval-style JSONL dataset into canonical task JSONL."
    )
    parser.add_argument(
        "--input", required=True, help="Path to TempEval-style JSONL input."
    )
    parser.add_argument(
        "--output", required=True, help="Path to canonical JSONL output."
    )
    parser.add_argument(
        "--category",
        default="tempeval_relation",
        help="Category label to assign to converted tasks.",
    )
    args = parser.parse_args()

    source_rows = load_jsonl(args.input)
    converted = [
        convert_tempeval_style_record(row, category=args.category)
        for row in source_rows
    ]
    _write_jsonl(Path(args.output), converted)
    print(f"Converted {len(converted)} tasks -> {args.output}")


if __name__ == "__main__":
    main()
