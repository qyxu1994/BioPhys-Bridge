"""Named alias for the duplicate-case_id guard (revision-v2 L229).

The canonical implementation lives in tests/test_no_duplicates.py; this file
re-exposes the duplicate-id assertion under the file name the revision spec
asks for so that test discovery surfaces both names.
"""

from __future__ import annotations

import copy

import pytest

from biophysevo.schemas.case_schema import validate_cases


def test_validate_cases_rejects_duplicate_case_ids(sample_case_dict):
    a = copy.deepcopy(sample_case_dict)
    b = copy.deepcopy(sample_case_dict)
    with pytest.raises(ValueError, match="Duplicate case_id"):
        validate_cases([a, b])


def test_validate_cases_accepts_distinct_case_ids(sample_case_dict):
    a = copy.deepcopy(sample_case_dict)
    b = copy.deepcopy(sample_case_dict)
    b["case_id"] = b["case_id"] + "_variant"
    validated = validate_cases([a, b])
    assert len({c.case_id for c in validated}) == 2
