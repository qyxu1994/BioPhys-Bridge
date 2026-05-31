"""Smoke evaluation outputs must never land in the release results folder."""

from __future__ import annotations

from biophysevo.utils.run_manager import RunManager


def test_smoke_run_dir_is_not_results_aggregate(tmp_path):
    """Smoke folders sit under runs/<ts>_quality_smoke/ — never under results/aggregate/."""
    run = RunManager.create(tmp_path / "runs", "quality_smoke")
    assert "quality_smoke" in run.run_dir.name
    assert run.run_dir.parent.name == "runs"
    assert "results" not in run.run_dir.parts
    assert "aggregate" not in run.run_dir.parts
    run.close()


def test_runmanager_creates_expected_layout(tmp_path):
    run = RunManager.create(
        tmp_path / "runs",
        "demo",
        config={"k": "v"},
        command="python -m demo",
    )
    assert (run.run_dir / "config.yaml").exists()
    assert (run.run_dir / "command.txt").exists()
    assert (run.run_dir / "checkpoints").is_dir()
    run.write_metrics({"x": 1})
    assert (run.run_dir / "metrics.json").exists()
    run.close()
