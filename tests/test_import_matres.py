"""Tests for scripts/import_matres.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.import_matres import (
    build_matres_tasks,
    load_matres_relations,
    load_timeml_documents,
    map_matres_relation,
)


def _write_timeml(path: Path, *, doc_id: str) -> None:
    path.write_text(
        f"""<?xml version="1.0" ?>
<TimeML>
<DOCID>{doc_id}</DOCID>
<TITLE>Example Title</TITLE>
<TEXT>
Alpha <EVENT eid="e1" class="OCCURRENCE">started</EVENT> yesterday.
Beta <EVENT eid="e2" class="OCCURRENCE">ended</EVENT> today.
Gamma <EVENT eid="e3" class="OCCURRENCE">matched</EVENT> later.
</TEXT>
<MAKEINSTANCE eventID="e1" eiid="ei1" tense="PAST" aspect="NONE" polarity="POS" pos="VERB" />
<MAKEINSTANCE eventID="e2" eiid="ei2" tense="PAST" aspect="NONE" polarity="POS" pos="VERB" />
<MAKEINSTANCE eventID="e3" eiid="ei3" tense="PAST" aspect="NONE" polarity="POS" pos="VERB" />
</TimeML>
""",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Relation mapping
# ---------------------------------------------------------------------------


def test_map_matres_relation_to_supported_labels() -> None:
    assert map_matres_relation("BEFORE") == "BEFORE"
    assert map_matres_relation("after") == "AFTER"
    assert map_matres_relation("EQUAL") == "SIMULTANEOUS"
    assert map_matres_relation("VAGUE") == "UNKNOWN"
    assert map_matres_relation("INCLUDES") is None


# ---------------------------------------------------------------------------
# MATRES loading and task building
# ---------------------------------------------------------------------------


def test_load_matres_relations_normalises_numeric_eiid(tmp_path: Path) -> None:
    matres_path = tmp_path / "timebank.txt"
    matres_path.write_text(
        "DOC1\tstarted\tended\t1\t2\tBEFORE\nDOC1\tended\tmatched\tei2\tei3\tEQUAL\n",
        encoding="utf-8",
    )

    rows, stats = load_matres_relations([str(matres_path)])

    assert [row.eiid1 for row in rows] == ["ei1", "ei2"]
    assert [row.eiid2 for row in rows] == ["ei2", "ei3"]
    assert [row.mapped_relation for row in rows] == ["BEFORE", "SIMULTANEOUS"]
    assert stats["raw_relation_counts"] == {"BEFORE": 1, "EQUAL": 1}


def test_build_matres_tasks_balances_labels_and_preserves_unknown(
    tmp_path: Path,
) -> None:
    timeml_root = tmp_path / "timeml"
    timeml_root.mkdir()
    _write_timeml(timeml_root / "DOC1.tml", doc_id="DOC1")
    matres_path = tmp_path / "timebank.txt"
    matres_path.write_text(
        "DOC1\tstarted\tended\t1\t2\tBEFORE\n"
        "DOC1\tended\tstarted\t2\t1\tAFTER\n"
        "DOC1\tended\tmatched\t2\t3\tEQUAL\n"
        "DOC1\tstarted\tmatched\t1\t3\tVAGUE\n",
        encoding="utf-8",
    )

    relations, _ = load_matres_relations([str(matres_path)])
    documents = load_timeml_documents(timeml_root)
    tasks, stats = build_matres_tasks(
        relations,
        documents,
        category="matres_temporal",
        context_radius=0,
        max_per_label=1,
        max_tasks=0,
        seed=7,
    )

    labels = sorted(task["gold_relations"][0][2] for task in tasks)
    assert labels == ["AFTER", "BEFORE", "SIMULTANEOUS", "UNKNOWN"]
    assert stats["sampled_counts"] == {
        "AFTER": 1,
        "BEFORE": 1,
        "SIMULTANEOUS": 1,
        "UNKNOWN": 1,
    }
    unknown_task = next(
        task for task in tasks if task["gold_relations"][0][2] == "UNKNOWN"
    )
    assert unknown_task["metadata"]["original_relation"] == "VAGUE"
    assert (
        "Use one of: BEFORE, AFTER, SIMULTANEOUS, UNKNOWN." in unknown_task["question"]
    )
    assert unknown_task["events"][0] in unknown_task["question"]
    assert unknown_task["events"][1] in unknown_task["question"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_help() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/import_matres.py", "--help"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert result.returncode == 0
