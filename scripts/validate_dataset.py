from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from src.dataset import load_jsonl
from src.dataset_validation import validate_tasks


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate a temporal reasoning JSONL dataset.")
    ap.add_argument("--data", required=True, help="Path to JSONL dataset.")
    ap.add_argument("--strict", action="store_true", help="Treat warnings as errors for key checks.")
    ap.add_argument(
        "--require-expected-fields",
        action="store_true",
        help="Require expected_valid and expected_consistent fields on every task.",
    )
    ap.add_argument("--out", default="", help="Optional path to write a validation report JSON.")
    args = ap.parse_args()

    tasks: List[Dict[str, Any]] = load_jsonl(args.data)
    rep = validate_tasks(
        tasks,
        strict=args.strict,
        require_expected_fields=args.require_expected_fields,
    )

    # Print summary
    print(f"Dataset: {args.data}")
    print(f"Tasks: {rep.num_tasks}")
    print(f"Errors: {rep.num_errors}")
    print(f"Warnings: {rep.num_warnings}")
    print("Category counts:")
    for k in sorted(rep.category_counts.keys()):
        print(f"  - {k}: {rep.category_counts[k]}")

    if rep.issues:
        print("\nIssues (first 25):")
        for it in rep.issues[:25]:
            print(f"- [{it.severity}] {it.task_id} {it.code}: {it.message}")

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_obj = {
            "num_tasks": rep.num_tasks,
            "num_errors": rep.num_errors,
            "num_warnings": rep.num_warnings,
            "category_counts": rep.category_counts,
            "issues": [
                {
                    "task_id": it.task_id,
                    "severity": it.severity,
                    "code": it.code,
                    "message": it.message,
                    "details": it.details,
                }
                for it in rep.issues
            ],
        }
        out_path.write_text(json.dumps(out_obj, indent=2), encoding="utf-8")
        print(f"\nWrote report: {out_path}")

    # Exit non-zero via exception if errors exist
    if rep.num_errors > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()