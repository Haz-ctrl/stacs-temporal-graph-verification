from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from scripts.run_llm_baseline import BaselineRunConfig, run_baseline


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def test_run_baseline_gold_mode_integration(tmp_path: Path) -> None:
    dataset_path = tmp_path / "eval.jsonl"
    _write_jsonl(
        dataset_path,
        [
            {
                "id": "amb_001",
                "category": "ambiguous",
                "question": "Sofia made tea in the classroom. Hana opened the door in the garden.",
                "events": [
                    "Sofia made tea in the classroom",
                    "Hana opened the door in the garden",
                ],
                "gold_relations": [],
                "expected_consistent": True,
                "expected_valid": True,
            },
            {
                "id": "lc_001",
                "category": "linear_chain",
                "question": "A happened. Afterwards, B happened. After that, C happened.",
                "events": ["A happened", "B happened", "C happened"],
                "gold_relations": [
                    ["A happened", "B happened", "BEFORE"],
                    ["B happened", "C happened", "BEFORE"],
                ],
                "expected_consistent": True,
                "expected_valid": True,
            },
            {
                "id": "con_001",
                "category": "contradiction",
                "question": "A happened before B, but B happened before A.",
                "events": ["A happened", "B happened"],
                "gold_relations": [
                    ["A happened", "B happened", "BEFORE"],
                    ["B happened", "A happened", "BEFORE"],
                ],
                "expected_consistent": False,
                "expected_valid": False,
            },
        ],
    )

    result = run_baseline(
        BaselineRunConfig(
            data_path=dataset_path,
            pred_source="gold",
            output_root=tmp_path / "runs",
        )
    )

    report = result.report
    assert report.num_tasks == 3
    assert report.num_failures == 0
    assert report.repair_hit_count == 0
    assert report.repair_hit_rate == 0.0
    assert report.parse_success_rate == 1.0
    assert report.conditional_validity_rate == 2 / 3
    assert report.parse_failure_counts == {}
    assert report.valid_count == 2
    assert report.invalid_count == 1
    assert report.run_config["specification_name"] == "default_temporal_spec"
    assert "ltl_contradiction" in report.formula_violation_counts
    assert report.first_violation_step_histogram == {"0": 1}
    assert report.dataset.expected_valid_tasks == 2
    assert report.dataset.expected_invalid_tasks == 1

    direct = report.metrics_expected_valid_only["direct"]
    closure = report.metrics_expected_valid_only["closure"]

    assert direct["precision"] == 1.0
    assert direct["recall"] == 1.0
    assert direct["f1"] == 1.0

    assert closure["precision"] == 1.0
    assert closure["recall"] == 1.0
    assert closure["f1"] == 1.0

    records = _read_jsonl(result.predictions_path)
    assert len(records) == 3
    assert records[0]["id"] == "amb_001"
    assert records[1]["id"] == "lc_001"
    assert records[2]["id"] == "con_001"
    assert records[0]["verification"]["specification_name"] == "default_temporal_spec"
    assert records[1]["verification"]["is_valid"] is True
    assert records[1]["verification"]["ltl_passed"] is True
    assert records[1]["verification"]["active_specification"]["formulas"] != []
    assert records[1]["score"]["preserves_ordering_closure"] is True


def test_run_baseline_noisy_mode_integration(tmp_path: Path) -> None:
    dataset_path = tmp_path / "eval.jsonl"
    _write_jsonl(
        dataset_path,
        [
            {
                "id": "amb_001",
                "category": "ambiguous",
                "question": "Sofia made tea in the classroom. Hana opened the door in the garden.",
                "events": [
                    "Sofia made tea in the classroom",
                    "Hana opened the door in the garden",
                ],
                "gold_relations": [],
                "expected_consistent": True,
                "expected_valid": True,
            },
            {
                "id": "lc_001",
                "category": "linear_chain",
                "question": "A happened. Afterwards, B happened. After that, C happened.",
                "events": ["A happened", "B happened", "C happened"],
                "gold_relations": [
                    ["A happened", "B happened", "BEFORE"],
                    ["B happened", "C happened", "BEFORE"],
                ],
                "expected_consistent": True,
                "expected_valid": True,
            },
        ],
    )

    result = run_baseline(
        BaselineRunConfig(
            data_path=dataset_path,
            pred_source="noisy",
            output_root=tmp_path / "runs",
            seed=7,
        )
    )

    report = result.report
    assert report.num_tasks == 2
    assert report.num_failures == 0
    assert report.repair_hit_count == 0
    assert report.parse_success_rate == 1.0
    assert report.conditional_validity_rate == 0.5
    assert report.parse_failure_counts == {}
    assert report.invalid_count >= 1
    assert report.violation_counts != {}
    assert report.formula_violation_counts != {}
    assert report.taxonomy_counts != {}
    assert report.overcommitment["num_gold_empty_tasks"] == 1
    assert report.overcommitment["num_overcommit_tasks"] == 1

    records = _read_jsonl(result.predictions_path)
    amb_record = next(record for record in records if record["id"] == "amb_001")
    assert amb_record["score"]["has_overcommitment"] is True


class FakeOllamaClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    def generate(self, model: str, prompt: str, temperature: float, seed: int | None) -> str:
        return """
        {
          "answer": "A happened before B.",
          "events": ["A happened", "B happened"],
          "relations": [["A happened", "B happened", "BEFORE"]],
          "reasoning_steps": [
            {
              "step_id": 1,
              "text": "The question states A happened before B.",
              "supports": [["A happened", "B happened", "BEFORE"]]
            }
          ]
        }
        """

    def tags_snapshot(self) -> list[str]:
        return ["fake-model:latest"]


def test_run_baseline_llm_mode_uses_structured_predictor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.run_llm_baseline as baseline_module

    monkeypatch.setattr(baseline_module, "OllamaClient", FakeOllamaClient)

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
                "expected_consistent": True,
                "expected_valid": True,
            }
        ],
    )

    result = run_baseline(
        BaselineRunConfig(
            data_path=dataset_path,
            pred_source="llm",
            output_root=tmp_path / "runs",
            model="fake-model",
            log_raw=True,
        )
    )

    report = result.report
    assert report.num_tasks == 1
    assert report.num_failures == 0
    assert report.repair_hit_count == 0
    assert report.parse_success_rate == 1.0
    assert report.conditional_validity_rate == 1.0
    assert report.parse_failure_counts == {}
    assert report.valid_count == 1
    assert report.invalid_count == 0
    assert report.model_metadata["prediction_mode"] == "structured_json"

    records = _read_jsonl(result.predictions_path)
    assert len(records) == 1
    record = records[0]
    assert record["answer"] == "A happened before B."
    assert record["pred_events"] == ["A happened", "B happened"]
    assert record["pred_edges"] == [["A happened", "B happened", "BEFORE"]]
    assert len(record["reasoning_steps"]) == 1
    assert record["reasoning_steps"][0]["step_id"] == 1
    assert "raw_output" in record
    assert record["verification"]["is_valid"] is True
    assert record["verification"]["ltl_passed"] is True
    assert record["verification"]["formula_violations"] == []


class FakeOllamaClientWithParseIssues:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self._responses = [
            """
            {
              "answer": "A happened before B."
              "events": ["A happened", "B happened"],
              "relations": [["A happened", "B happened", "BEFORE"]],
              "reasoning_steps": []
            }
            """,
            """{ "answer": "broken" """,
            """
            {
              "answer": "A happened before B.",
              "events": ["A happened", "B happened"],
              "relations": [],
              "reasoning_steps": [
                {
                  "step_id": 1,
                  "text": "bad support",
                  "supports": [["A happened"]]
                }
              ]
            }
            """,
            """
            {
              "answer": 123,
              "events": ["A happened", "B happened"],
              "relations": []
            }
            """,
        ]

    def generate(self, model: str, prompt: str, temperature: float, seed: int | None) -> str:
        return self._responses.pop(0)

    def tags_snapshot(self) -> list[str]:
        return ["fake-model:latest"]


def test_run_baseline_reports_parse_failure_taxonomy_and_conditional_validity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import scripts.run_llm_baseline as baseline_module

    monkeypatch.setattr(baseline_module, "OllamaClient", FakeOllamaClientWithParseIssues)

    dataset_path = tmp_path / "eval.jsonl"
    _write_jsonl(
        dataset_path,
        [
            {
                "id": "ok_001",
                "category": "linear_chain",
                "question": "A happened before B.",
                "events": ["A happened", "B happened"],
                "gold_relations": [["A happened", "B happened", "BEFORE"]],
                "expected_consistent": True,
                "expected_valid": True,
            },
            {
                "id": "bad_json_001",
                "category": "linear_chain",
                "question": "A happened before B.",
                "events": ["A happened", "B happened"],
                "gold_relations": [["A happened", "B happened", "BEFORE"]],
                "expected_consistent": True,
                "expected_valid": True,
            },
            {
                "id": "bad_edge_001",
                "category": "linear_chain",
                "question": "A happened before B.",
                "events": ["A happened", "B happened"],
                "gold_relations": [["A happened", "B happened", "BEFORE"]],
                "expected_consistent": True,
                "expected_valid": True,
            },
            {
                "id": "schema_001",
                "category": "linear_chain",
                "question": "A happened before B.",
                "events": ["A happened", "B happened"],
                "gold_relations": [["A happened", "B happened", "BEFORE"]],
                "expected_consistent": True,
                "expected_valid": True,
            },
        ],
    )

    result = run_baseline(
        BaselineRunConfig(
            data_path=dataset_path,
            pred_source="llm",
            output_root=tmp_path / "runs",
            model="fake-model",
            log_raw=True,
        )
    )

    report = result.report
    assert report.num_tasks == 4
    assert report.num_failures == 3
    assert report.repair_hit_count == 1
    assert report.repair_hit_rate == 0.25
    assert report.parse_success_rate == 0.25
    assert report.conditional_validity_rate == 1.0
    assert report.parse_failure_counts == {
        "invalid_json": 1,
        "invalid_edge_support": 1,
        "schema_violation": 1,
    }

    assert [failure["category"] for failure in report.failures] == [
        "invalid_json",
        "invalid_edge_support",
        "schema_violation",
    ]
    assert all(failure["task_category"] == "linear_chain" for failure in report.failures)
    assert all("raw_output" in failure for failure in report.failures)
