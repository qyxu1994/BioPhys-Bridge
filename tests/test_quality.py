"""Quality validation CLI + aggregate metrics."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from biophysevo.quality.deduplicate import find_duplicate_case_ids
from biophysevo.quality.license_check import has_license, normalize_license
from biophysevo.quality.scoring import aggregate_metrics, per_case_score
from biophysevo.quality.validate_cases import main as validate_main
from biophysevo.schemas.case_schema import Case


def test_per_case_score_on_sample(sample_case_dict):
    case = Case.model_validate(sample_case_dict)
    score = per_case_score(case)
    assert 0.0 < score <= 1.0


def test_aggregate_metrics_basic(sample_case_dict):
    case = Case.model_validate(sample_case_dict)
    m = aggregate_metrics([case], n_raw=1)
    assert m["n_valid"] == 1
    assert m["schema_valid_rate"] == 1.0
    assert m["quantitative_evidence_rate"] == 1.0
    assert m["duplicate_rate"] == 0.0


def test_validate_cli_writes_report_and_outputs(tmp_path, sample_case_dict):
    input_path = tmp_path / "cases_draft.jsonl"
    input_path.write_text(json.dumps(sample_case_dict) + "\n")
    out_path = tmp_path / "cases_validated.jsonl"
    report_path = tmp_path / "report.json"

    rc = validate_main([
        "--input", str(input_path),
        "--out", str(out_path),
        "--report", str(report_path),
        "--run-dir", str(tmp_path / "runs" / "val"),
    ])
    assert rc == 0
    assert out_path.exists()
    assert report_path.exists()
    report = json.loads(report_path.read_text())
    assert report["n_valid"] == 1


def test_validate_cli_fails_on_duplicate_ids(tmp_path, sample_case_dict):
    a = copy.deepcopy(sample_case_dict)
    b = copy.deepcopy(sample_case_dict)
    input_path = tmp_path / "cases_draft.jsonl"
    input_path.write_text(json.dumps(a) + "\n" + json.dumps(b) + "\n")
    out_path = tmp_path / "cases_validated.jsonl"
    report_path = tmp_path / "report.json"

    rc = validate_main([
        "--input", str(input_path),
        "--out", str(out_path),
        "--report", str(report_path),
        "--run-dir", str(tmp_path / "runs" / "val2"),
    ])
    assert rc == 1


def test_license_check_flags_missing(make_case):
    # has_license operates on a Case object — use a fresh valid one and lower-case
    c = Case.model_validate(make_case())
    assert has_license(c)
    # simulate a case object via model_copy with a known-bad license value
    c2 = c.model_copy(update={"source": c.source.model_copy(update={"license": "unknown"})})
    assert not has_license(c2)


def test_license_normalization_aliases(make_case):
    raw = make_case()
    raw["source"]["license"] = "cc by"
    case = Case.model_validate(raw)
    assert case.source.license == "CC-BY-4.0"
    assert normalize_license("cc0") == "CC0-1.0"
