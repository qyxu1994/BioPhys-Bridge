"""Duplicate-id guard for batched validation and JSONL dedup."""

from __future__ import annotations

import pytest

from biophysevo.schemas.case_schema import validate_cases
from biophysevo.utils.hashing import deterministic_id
from biophysevo.utils.io import dedup_by_id


def test_validate_cases_rejects_duplicate_case_ids(sample_case_dict):
    import copy

    a = copy.deepcopy(sample_case_dict)
    b = copy.deepcopy(sample_case_dict)
    with pytest.raises(ValueError, match="Duplicate case_id"):
        validate_cases([a, b])


def test_dedup_by_id_keeps_first_occurrence():
    rs = [{"id": "x", "v": 1}, {"id": "x", "v": 2}, {"id": "y", "v": 3}]
    out = dedup_by_id(rs)
    assert [r["v"] for r in out] == [1, 3]


def test_deterministic_id_is_stable():
    a = deterministic_id({"k": 1, "v": [1, 2, 3]})
    b = deterministic_id({"v": [1, 2, 3], "k": 1})
    assert a == b
    c = deterministic_id({"v": [1, 2, 4], "k": 1})
    assert a != c
