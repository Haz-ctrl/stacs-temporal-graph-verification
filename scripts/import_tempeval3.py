from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List

from src.benchmark_adapters import convert_tempeval3_tml_file


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert TempEval-3 TimeML files into canonical event-event evaluation tasks."
    )
    parser.add_argument(
        "--input-root",
        required=True,
        help="Root directory of an extracted TempEval-3 corpus containing split subdirectories such as test/.",
    )
    parser.add_argument(
        "--split",
        action="append",
        default=[],
        help="Split directory to convert. Repeatable. Defaults to test.",
    )
    parser.add_argument("--output", required=True, help="Output canonical JSONL path.")
    parser.add_argument(
        "--stats-out",
        default="",
        help="Optional JSON path for conversion statistics.",
    )
    parser.add_argument(
        "--category",
        default="tempeval_relation",
        help="Category label to assign to converted tasks.",
    )
    args = parser.parse_args()

    input_root = Path(args.input_root)
    splits = args.split or ["test"]
    tasks: List[Dict[str, Any]] = []
    relation_counts: Counter[str] = Counter()
    split_stats: List[Dict[str, Any]] = []

    for split in splits:
        split_root = input_root / split
        if not split_root.is_dir():
            raise ValueError(f"Split directory not found: {split_root}")
        for path in sorted(split_root.rglob("*.tml")):
            bundle = convert_tempeval3_tml_file(path, split=split, category=args.category)
            tasks.extend(bundle.tasks)
            split_stats.append(bundle.stats)
            for task in bundle.tasks:
                relation_counts[task["gold_relations"][0][2]] += 1

    _write_jsonl(Path(args.output), tasks)
    if args.stats_out:
        stats_payload = {
            "input_root": str(input_root),
            "splits": splits,
            "num_tasks": len(tasks),
            "relation_counts": dict(sorted(relation_counts.items())),
            "documents": split_stats,
        }
        Path(args.stats_out).write_text(json.dumps(stats_payload, indent=2), encoding="utf-8")
    print(f"Converted {len(tasks)} tasks -> {args.output}")


if __name__ == "__main__":
    main()
