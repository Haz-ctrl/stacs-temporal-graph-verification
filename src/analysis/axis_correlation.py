"""
Intrinsic-axis correlation analysis for temporal verification runs.

Computes pairwise Pearson and phi (Matthews) correlations across binary
intrinsic axes (parse_success, verifier_valid, trace_grounded). For binary
variables phi == Pearson, but we report both so the dissertation can name
the more interpretable coefficient for the binary-only subset.

Saves per-run CSV and heatmap PNG alongside the existing analysis artefacts.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BINARY_AXES: Tuple[str, ...] = ("parse_success", "verifier_valid", "trace_grounded")


@dataclass(frozen=True)
class AxisCorrelationResult:
    axes: Tuple[str, ...]
    # (axis_a, axis_b) -> Pearson r; NaN when one variable is constant
    pearson: Dict[Tuple[str, str], float]
    # phi coefficient (Matthews) for the binary subset; equals pearson for binary vars
    phi: Dict[Tuple[str, str], float]
    # count of tasks where both flags agree (both True or both False)
    agreement: Dict[Tuple[str, str], int]
    n: int


def extract_flags(
    predictions: Sequence[Mapping[str, Any]],
    failures: Sequence[Mapping[str, Any]],
) -> List[Dict[str, bool]]:
    """Build a per-task list of binary intrinsic flags from run data."""
    rows: List[Dict[str, bool]] = []
    for pred in predictions:
        v = pred.get("verification", {})
        rows.append(
            {
                "parse_success": True,
                "verifier_valid": bool(v.get("is_valid", False)),
                # Fall back to absence-of-trace-violations when field missing (older runs)
                "trace_grounded": bool(v.get("trace_grounded", True)),
            }
        )
    for _ in failures:
        # Parse/transport failures: no valid graph, no grounded trace
        rows.append(
            {"parse_success": False, "verifier_valid": False, "trace_grounded": False}
        )
    return rows


def _pearson(xs: List[int], ys: List[int]) -> Optional[float]:
    """Pearson r between two equal-length integer (0/1) sequences."""
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0.0 or dy == 0.0:
        # One variable is constant across all tasks; correlation is undefined.
        return None
    return num / (dx * dy)


def compute_axis_correlation(
    flags: Sequence[Dict[str, bool]],
    *,
    axes: Tuple[str, ...] = BINARY_AXES,
) -> AxisCorrelationResult:
    """Compute pairwise Pearson/phi matrices and agreement counts."""
    pearson: Dict[Tuple[str, str], float] = {}
    phi: Dict[Tuple[str, str], float] = {}
    agreement: Dict[Tuple[str, str], int] = {}
    n = len(flags)

    axis_list = list(axes)
    for i, a in enumerate(axis_list):
        for b in axis_list[i + 1 :]:
            xs = [int(f[a]) for f in flags]
            ys = [int(f[b]) for f in flags]
            r = _pearson(xs, ys)
            val = r if r is not None else float("nan")
            pearson[(a, b)] = val
            # phi == Pearson for binary variables; named separately for readability
            phi[(a, b)] = val
            agreement[(a, b)] = sum(1 for f in flags if f[a] == f[b])

    return AxisCorrelationResult(
        axes=tuple(axis_list), pearson=pearson, phi=phi, agreement=agreement, n=n
    )


def axis_correlation_prose(result: AxisCorrelationResult) -> str:
    """
    Generate a factually neutral prose summary of axis correlations for report.md.
    Reports collinear pairs, strongest, and weakest correlations.
    """
    valid_pairs = [
        (abs(v), a, b, v)
        for (a, b), v in result.pearson.items()
        if not math.isnan(v)
    ]
    if not valid_pairs:
        return ""

    valid_pairs.sort(reverse=True)
    lines: List[str] = []

    collinear = [(a, b, v) for _, a, b, v in valid_pairs if abs(v) > 0.9]
    if collinear:
        names = ", ".join(
            f"`{a}`–`{b}` (ρ = {v:.2f})" for a, b, v in collinear
        )
        lines.append(
            f"Collinear axis pairs (|ρ| > 0.90): {names}. "
            "These axes provide largely redundant signal and should not be "
            "treated as independent evidence."
        )

    strongest = valid_pairs[0]
    weakest = valid_pairs[-1]
    lines.append(
        f"Strongest pairwise correlation: `{strongest[1]}`–`{strongest[2]}` "
        f"at ρ = {strongest[3]:.2f} (n = {result.n})."
    )
    lines.append(
        f"Weakest pairwise correlation: `{weakest[1]}`–`{weakest[2]}` "
        f"at ρ = {weakest[3]:.2f}."
    )

    return " ".join(lines)


def save_axis_correlation_csv(result: AxisCorrelationResult, path: Path) -> None:
    """Write pairwise correlation stats to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    axes = list(result.axes)
    rows: List[Dict[str, object]] = []
    for i, a in enumerate(axes):
        for b in axes[i + 1 :]:
            pair = (a, b)
            rows.append(
                {
                    "axis_a": a,
                    "axis_b": b,
                    "pearson_r": result.pearson.get(pair, float("nan")),
                    "phi": result.phi.get(pair, float("nan")),
                    "agreement_count": result.agreement.get(pair, 0),
                    "n": result.n,
                }
            )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)


def plot_axis_correlation(result: AxisCorrelationResult, path: Path) -> None:
    """Save a matplotlib heatmap of the Pearson correlation matrix."""
    axes = list(result.axes)
    n_axes = len(axes)

    # Build full symmetric matrix for display (diagonal = 1.0)
    matrix = [[1.0 if i == j else 0.0 for j in range(n_axes)] for i in range(n_axes)]
    for i, a in enumerate(axes):
        for j, b in enumerate(axes):
            if i == j:
                continue
            pair = (a, b) if i < j else (b, a)
            val = result.pearson.get(pair, float("nan"))
            matrix[i][j] = val

    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(matrix, vmin=-1, vmax=1, cmap="coolwarm", aspect="auto")
    plt.colorbar(im, ax=ax, label="Pearson ρ")

    ax.set_xticks(range(n_axes))
    ax.set_yticks(range(n_axes))
    ax.set_xticklabels(axes, rotation=30, ha="right", fontsize=9)
    ax.set_yticklabels(axes, fontsize=9)
    ax.set_title(f"Intrinsic axis correlations (n = {result.n})", fontsize=10)

    for i in range(n_axes):
        for j in range(n_axes):
            val = matrix[i][j]
            label = f"{val:.2f}" if not math.isnan(val) else "n/a"
            ax.text(j, i, label, ha="center", va="center", fontsize=8,
                    color="black" if abs(val) < 0.6 else "white")

    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)
