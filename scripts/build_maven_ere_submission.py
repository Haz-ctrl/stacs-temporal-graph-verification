"""
Build a MAVEN-ERE CodaLab submission from pairwise prediction records.

This script expects prediction records generated from canonical MAVEN-ERE test
tasks created by `scripts/import_maven_ere.py --split test`.

The resulting archive follows the upstream submission convention:
  - `test_prediction.jsonl`
  - zipped into `submission.zip`

Unsupported competition tracks are emitted empty by default:
  - `coreference`
  - `causal_relations`
  - `subevent_relations`

Temporal predictions are reconstructed from pairwise verifier outputs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List
from zipfile import ZIP_DEFLATED, ZipFile


TEMPORAL_BUCKETS = ("BEFORE", "OVERLAP", "CONTAINS", "SIMULTANEOUS", "ENDS-ON", "BEGINS-ON")


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _derive_temporal_label(record: Dict[str, Any]) -> str:
    pred_edges = list(record.get("pred_edges", []))
    events = list(record.get("events", []))
    if len(events) != 2:
        return "UNKNOWN"

    source_label, target_label = events
    if [source_label, target_label, "SIMULTANEOUS"] in pred_edges:
        return "SIMULTANEOUS"
    if [source_label, target_label, "BEFORE"] in pred_edges:
        return "BEFORE"
    if [source_label, target_label, "AFTER"] in pred_edges:
        return "AFTER"
    return "UNKNOWN"


def build_submission_rows(
    *,
    test_docs: Iterable[Dict[str, Any]],
    predictions: Iterable[Dict[str, Any]],
    simultaneous_label: str,
) -> List[Dict[str, Any]]:
    by_doc: Dict[str, Dict[str, Any]] = {}
    for doc in test_docs:
        by_doc[str(doc["id"])] = {
            "id": str(doc["id"]),
            "coreference": [],
            "temporal_relations": {label: [] for label in TEMPORAL_BUCKETS},
            "causal_relations": {"CAUSE": [], "PRECONDITION": []},
            "subevent_relations": [],
        }

    seen_temporal_pairs: set[tuple[str, str, str]] = set()
    for record in predictions:
        metadata = dict(record.get("metadata", {}))
        doc_id = str(metadata.get("document_id", ""))
        if doc_id not in by_doc:
            continue

        source_node_id = str(metadata.get("source_node_id", ""))
        target_node_id = str(metadata.get("target_node_id", ""))
        if not source_node_id or not target_node_id or source_node_id == target_node_id:
            continue

        label = _derive_temporal_label(record)
        if label == "UNKNOWN":
            continue

        if label == "AFTER":
            bucket = "BEFORE"
            pair = (target_node_id, source_node_id)
        elif label == "SIMULTANEOUS":
            bucket = simultaneous_label
            pair = (source_node_id, target_node_id)
        else:
            bucket = "BEFORE"
            pair = (source_node_id, target_node_id)

        dedupe_key = (doc_id, bucket, pair[0], pair[1])
        if dedupe_key in seen_temporal_pairs:
            continue
        seen_temporal_pairs.add(dedupe_key)
        by_doc[doc_id]["temporal_relations"][bucket].append([pair[0], pair[1]])

    return [by_doc[doc_id] for doc_id in sorted(by_doc)]


def write_submission(
    *,
    output_jsonl: Path,
    output_zip: Path,
    rows: Iterable[Dict[str, Any]],
) -> None:
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    with output_jsonl.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    with ZipFile(output_zip, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(output_jsonl, arcname="test_prediction.jsonl")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a MAVEN-ERE CodaLab submission.zip from pairwise prediction records."
    )
    parser.add_argument("--test-docs", required=True, help="Raw MAVEN-ERE test.jsonl path.")
    parser.add_argument(
        "--predictions",
        required=True,
        help="Pairwise predictions JSONL emitted by the baseline runner on converted MAVEN-ERE test tasks.",
    )
    parser.add_argument(
        "--output-jsonl",
        default="test_prediction.jsonl",
        help="Path to write the CodaLab submission JSONL file.",
    )
    parser.add_argument(
        "--output-zip",
        default="submission.zip",
        help="Path to write the zipped submission archive.",
    )
    parser.add_argument(
        "--simultaneous-label",
        choices=["SIMULTANEOUS", "OVERLAP"],
        default="SIMULTANEOUS",
        help="Bucket to use for local SIMULTANEOUS predictions in MAVEN-ERE output.",
    )
    args = parser.parse_args()

    rows = build_submission_rows(
        test_docs=_load_jsonl(Path(args.test_docs)),
        predictions=_load_jsonl(Path(args.predictions)),
        simultaneous_label=args.simultaneous_label,
    )
    write_submission(
        output_jsonl=Path(args.output_jsonl),
        output_zip=Path(args.output_zip),
        rows=rows,
    )
    print(f"Wrote MAVEN-ERE submission -> {args.output_zip}")


if __name__ == "__main__":
    main()
