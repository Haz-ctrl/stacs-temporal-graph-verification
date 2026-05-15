from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts import run_model_sweep


# ---------------------------------------------------------------------------
# Successful sweeps
# ---------------------------------------------------------------------------


def test_run_model_sweep_writes_manifest_and_index(
    tmp_path: Path,
    monkeypatch,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            [
                {
                    "model": "model-a",
                    "label": "Model A",
                    "family": "alpha",
                    "size": "7b",
                    "reasoning_tuned": True,
                },
                {
                    "model": "model-b",
                    "label": "Model B",
                    "family": "beta",
                    "size": "9b",
                    "reasoning_tuned": False,
                },
            ]
        ),
        encoding="utf-8",
    )

    created_runs: list[str] = []

    class FakeResult:
        def __init__(self, run_id: str, run_dir: Path) -> None:
            self.run_id = run_id
            self.run_dir = run_dir

    def fake_run_baseline(config):  # type: ignore[no-untyped-def]
        run_id = f"run_{len(created_runs) + 1}"
        run_dir = Path(config.output_root) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        created_runs.append(run_id)
        return FakeResult(run_id, run_dir)

    monkeypatch.setattr(run_model_sweep, "run_baseline", fake_run_baseline)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_model_sweep.py",
            "--manifest",
            str(manifest_path),
            "--output-root",
            str(tmp_path / "runs"),
        ],
    )

    run_model_sweep.main()

    run_manifest = json.loads(
        (tmp_path / "runs" / "run_manifest.json").read_text(encoding="utf-8")
    )
    sweep_index = json.loads(
        (tmp_path / "runs" / "sweep_index.json").read_text(encoding="utf-8")
    )

    assert sorted(run_manifest["runs"].keys()) == ["run_1", "run_2"]
    assert run_manifest["runs"]["run_1"]["model_label"] == "Model A"
    assert sweep_index["runs"][1]["label"] == "Model B"
    assert sweep_index["runs"][0]["status"] == "completed"
    assert sweep_index["failures"] == []


# ---------------------------------------------------------------------------
# Failure handling
# ---------------------------------------------------------------------------


def test_run_model_sweep_continues_on_error(
    tmp_path: Path,
    monkeypatch,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            [
                {"model": "model-a", "label": "Model A"},
                {"model": "model-b", "label": "Model B"},
            ]
        ),
        encoding="utf-8",
    )

    class FakeResult:
        def __init__(self, run_id: str, run_dir: Path) -> None:
            self.run_id = run_id
            self.run_dir = run_dir

    def fake_run_baseline(config):  # type: ignore[no-untyped-def]
        if config.model == "model-a":
            raise TimeoutError("model timed out")
        run_dir = Path(config.output_root) / "run_2"
        run_dir.mkdir(parents=True, exist_ok=True)
        return FakeResult("run_2", run_dir)

    monkeypatch.setattr(run_model_sweep, "run_baseline", fake_run_baseline)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_model_sweep.py",
            "--manifest",
            str(manifest_path),
            "--output-root",
            str(tmp_path / "runs"),
            "--continue-on-error",
        ],
    )

    run_model_sweep.main()

    run_manifest = json.loads(
        (tmp_path / "runs" / "run_manifest.json").read_text(encoding="utf-8")
    )
    sweep_index = json.loads(
        (tmp_path / "runs" / "sweep_index.json").read_text(encoding="utf-8")
    )

    assert run_manifest["failures"][0]["model"] == "model-a"
    assert run_manifest["runs"]["run_2"]["status"] == "completed"
    assert sweep_index["runs"][0]["status"] == "failed"
    assert sweep_index["runs"][1]["status"] == "completed"
