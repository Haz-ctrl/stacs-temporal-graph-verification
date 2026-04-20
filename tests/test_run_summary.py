from __future__ import annotations

import json
from pathlib import Path

from scripts.run_llm_baseline import BaselineRunConfig, run_baseline
from src.run_summary import summarise_runs


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def test_summarise_runs_generates_tables_and_plots(tmp_path: Path) -> None:
    dataset_path = tmp_path / "eval.jsonl"
    _write_jsonl(
        dataset_path,
        [
            {
                "id": "amb_001",
                "category": "ambiguous",
                "question": "A happened. B happened.",
                "events": ["A happened", "B happened"],
                "gold_relations": [],
                "expected_valid": True,
                "expected_consistent": True,
            },
            {
                "id": "lc_001",
                "category": "linear_chain",
                "question": "A happened before B.",
                "events": ["A happened", "B happened"],
                "gold_relations": [["A happened", "B happened", "BEFORE"]],
                "expected_valid": True,
                "expected_consistent": True,
            },
        ],
    )

    gold_run = run_baseline(
        BaselineRunConfig(
            data_path=dataset_path,
            pred_source="gold",
            output_root=tmp_path / "runs",
        )
    )
    noisy_run = run_baseline(
        BaselineRunConfig(
            data_path=dataset_path,
            pred_source="noisy",
            output_root=tmp_path / "runs",
            seed=7,
        )
    )

    manifest_path = tmp_path / "run_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "runs": {
                    gold_run.run_id: {"model_label": "gold-baseline", "family": "control"},
                    noisy_run.run_id: {"model_label": "noisy-baseline", "family": "control"},
                }
            }
        ),
        encoding="utf-8",
    )

    out_dir = tmp_path / "analysis"
    result = summarise_runs(
        [gold_run.run_dir, noisy_run.run_dir],
        out_dir=out_dir,
        manifest_path=manifest_path,
    )

    assert len(result["summary"]) == 2
    assert (out_dir / "summary.csv").exists()
    assert (out_dir / "category_breakdown.csv").exists()
    assert (out_dir / "difficulty_breakdown.csv").exists()
    assert (out_dir / "failure_breakdown.csv").exists()
    assert (out_dir / "report.md").exists()
    assert (out_dir / "counterexamples.md").exists()
    assert (out_dir / "plots" / "parse_success_rate.png").exists()
    assert (out_dir / "plots" / "direct_vs_closure_f1.png").exists()
    assert (out_dir / "plots" / "ambiguity_behaviour.png").exists()
    assert (out_dir / "plots" / "contradiction_detection_rate.png").exists()
    assert (out_dir / "plots" / "validity_expectation_alignment_rate.png").exists()
    assert (out_dir / "plots" / "verification_task_incidence.png").exists()
    assert any(row["model_label"] == "gold-baseline" for row in result["summary"])
    assert any(row["category"] == "ambiguous" for row in result["category_breakdown"])
    assert any(row["difficulty"] == "empty_gold" for row in result["difficulty_breakdown"])
    gold_row = next(row for row in result["summary"] if row["model_label"] == "gold-baseline")
    assert gold_row["parse_success_ci_low"] is not None
    assert gold_row["validity_expectation_alignment_rate"] == 1.0
    assert gold_row["validity_expectation_alignment_rate_e2e"] == 1.0
    assert gold_row["avg_first_violation_step"] is None
    assert gold_row["fidelity_direct_f1"] == 1.0
    assert gold_row["fidelity_closure_f1"] == 1.0
    ambiguous_row = next(
        row for row in result["category_breakdown"]
        if row["model_label"] == "gold-baseline" and row["category"] == "ambiguous"
    )
    assert ambiguous_row["direct_f1"] is None


def test_summarise_runs_auto_loads_run_manifest(tmp_path: Path) -> None:
    dataset_path = tmp_path / "eval.jsonl"
    _write_jsonl(
        dataset_path,
        [
            {
                "id": "lc_001",
                "category": "linear_chain",
                "question": "A happened before B.",
                "events": ["A happened", "B happened"],
                "gold_relations": [["A happened", "B happened", "BEFORE"]],
                "expected_valid": True,
                "expected_consistent": True,
            },
        ],
    )

    run = run_baseline(
        BaselineRunConfig(
            data_path=dataset_path,
            pred_source="gold",
            output_root=tmp_path / "runs",
        )
    )

    manifest_path = (tmp_path / "runs") / "run_manifest.json"
    manifest_path.write_text(
        json.dumps({"runs": {run.run_id: {"model_label": "gold-auto"}}}),
        encoding="utf-8",
    )

    result = summarise_runs([run.run_dir], out_dir=tmp_path / "analysis")
    assert result["summary"][0]["model_label"] == "gold-auto"
