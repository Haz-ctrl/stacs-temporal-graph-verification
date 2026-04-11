from __future__ import annotations

import argparse
from pathlib import Path

from src.run_summary import summarise_runs


def _resolve_run_dirs(inputs: list[str]) -> list[Path]:
    run_dirs: list[Path] = []
    for item in inputs:
        path = Path(item)
        if (path / "report.json").exists():
            run_dirs.append(path)
            continue
        if path.is_dir():
            run_dirs.extend(
                sorted(
                    child for child in path.iterdir()
                    if child.is_dir() and (child / "report.json").exists()
                )
            )
            continue
        raise ValueError(f"Input path is not a run directory or run-root directory: {path}")
    return run_dirs


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarise one or more temporal verification runs.")
    parser.add_argument(
        "--runs",
        nargs="+",
        required=True,
        help="Run directories or parent directories containing run directories.",
    )
    parser.add_argument("--out", required=True, help="Output directory for tables, plots, and markdown.")
    parser.add_argument(
        "--manifest",
        default="",
        help="Optional run manifest JSON mapping run IDs to labels and groups.",
    )
    args = parser.parse_args()

    run_dirs = _resolve_run_dirs(args.runs)
    summarise_runs(
        run_dirs,
        out_dir=args.out,
        manifest_path=args.manifest or None,
    )
    print(f"Summarised {len(run_dirs)} runs -> {args.out}")


if __name__ == "__main__":
    main()
