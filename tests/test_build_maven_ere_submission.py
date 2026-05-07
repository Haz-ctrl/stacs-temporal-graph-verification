"""Tests for scripts/build_maven_ere_submission.py."""
from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

from scripts.build_maven_ere_submission import build_submission_rows, write_submission


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def test_build_submission_rows_maps_before_after_and_unknown() -> None:
    test_docs = [{"id": "doc-1"}, {"id": "doc-2"}]
    predictions = [
        {
            "events": ["A [m1]", "B [m2]"],
            "pred_edges": [["A [m1]", "B [m2]", "BEFORE"]],
            "metadata": {"document_id": "doc-1", "source_node_id": "m1", "target_node_id": "m2"},
        },
        {
            "events": ["C [m3]", "D [m4]"],
            "pred_edges": [["C [m3]", "D [m4]", "AFTER"]],
            "metadata": {"document_id": "doc-1", "source_node_id": "m3", "target_node_id": "m4"},
        },
        {
            "events": ["E [m5]", "F [m6]"],
            "pred_edges": [["E [m5]", "F [m6]", "SIMULTANEOUS"]],
            "metadata": {"document_id": "doc-2", "source_node_id": "m5", "target_node_id": "m6"},
        },
    ]

    rows = build_submission_rows(
        test_docs=test_docs,
        predictions=predictions,
        simultaneous_label="SIMULTANEOUS",
    )

    doc1 = next(row for row in rows if row["id"] == "doc-1")
    doc2 = next(row for row in rows if row["id"] == "doc-2")

    assert doc1["temporal_relations"]["BEFORE"] == [["m1", "m2"], ["m4", "m3"]]
    assert doc2["temporal_relations"]["SIMULTANEOUS"] == [["m5", "m6"]]
    assert doc1["causal_relations"] == {"CAUSE": [], "PRECONDITION": []}
    assert doc2["subevent_relations"] == []


def test_write_submission_creates_zip(tmp_path: Path) -> None:
    output_jsonl = tmp_path / "test_prediction.jsonl"
    output_zip = tmp_path / "submission.zip"
    rows = [
        {
            "id": "doc-1",
            "coreference": [],
            "temporal_relations": {
                "BEFORE": [],
                "OVERLAP": [],
                "CONTAINS": [],
                "SIMULTANEOUS": [],
                "ENDS-ON": [],
                "BEGINS-ON": [],
            },
            "causal_relations": {"CAUSE": [], "PRECONDITION": []},
            "subevent_relations": [],
        }
    ]

    write_submission(output_jsonl=output_jsonl, output_zip=output_zip, rows=rows)

    assert output_jsonl.exists()
    assert output_zip.exists()
    with ZipFile(output_zip) as archive:
        assert archive.namelist() == ["test_prediction.jsonl"]
