"""eval_quality smoke/full mode behavior."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from biophysevo.evaluation.eval_quality import main as eval_main


def _write_input(tmp_path: Path, cases: list[dict]) -> Path:
    p = tmp_path / "cases.jsonl"
    p.write_text("\n".join(json.dumps(c) for c in cases) + "\n")
    return p


def test_smoke_writes_to_runs_not_results(tmp_path, sample_case_dict):
    inp = _write_input(tmp_path, [sample_case_dict])
    smoke_dir = tmp_path / "runs" / "smoke"
    rc = eval_main([
        "--input", str(inp),
        "--mode", "smoke",
        "--run-dir", str(smoke_dir),
    ])
    assert rc == 0
    assert (smoke_dir / "per_case.jsonl").exists()
    assert (smoke_dir / "metrics.json").exists()
    assert not (tmp_path / "results" / "aggregate").exists()


def test_full_refuses_existing_output_dir(tmp_path, sample_case_dict):
    inp = _write_input(tmp_path, [sample_case_dict])
    full_out = tmp_path / "results_full"
    full_out.mkdir()
    rc = eval_main([
        "--input", str(inp),
        "--mode", "full",
        "--full-results-dir", str(full_out),
    ])
    assert rc == 2


def test_full_refuses_duplicate_case_ids(tmp_path, sample_case_dict):
    a = copy.deepcopy(sample_case_dict)
    b = copy.deepcopy(sample_case_dict)
    inp = _write_input(tmp_path, [a, b])
    full_out = tmp_path / "results_full"
    rc = eval_main([
        "--input", str(inp),
        "--mode", "full",
        "--full-results-dir", str(full_out),
    ])
    assert rc == 2


def test_full_runs_clean(tmp_path, sample_case_dict):
    inp = _write_input(tmp_path, [sample_case_dict])
    full_out = tmp_path / "results_aggregate"
    rc = eval_main([
        "--input", str(inp),
        "--mode", "full",
        "--full-results-dir", str(full_out),
    ])
    assert rc == 0
    assert (full_out / "quality_metrics.json").exists()
    metrics = json.loads((full_out / "quality_metrics.json").read_text())
    assert metrics["mode"] == "full"
