"""Direct tests for quality.validate_schema.validate_each."""

from __future__ import annotations

from biophysevo.quality.validate_schema import validate_each


def test_validate_each_all_valid(sample_case_dict):
    valid, errors = validate_each([sample_case_dict])
    assert len(valid) == 1
    assert errors == []


def test_validate_each_collects_errors_with_index_and_case_id(make_case, sample_case_dict):
    bad = make_case()
    bad["case_id"] = "bad id with spaces"  # fails CASE_ID_RE
    raw = [sample_case_dict, bad]

    valid, errors = validate_each(raw)

    assert len(valid) == 1  # the good one still parses
    assert len(errors) == 1
    err = errors[0]
    assert err["index"] == 1
    assert err["case_id"] == "bad id with spaces"
    assert "case_id" in err["error"]


def test_validate_each_empty_input():
    valid, errors = validate_each([])
    assert valid == []
    assert errors == []
