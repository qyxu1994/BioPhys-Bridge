"""physical_interpretation is required on every Case (revision-v2 L100-106)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from biophysevo.schemas.case_schema import Case


def test_missing_physical_interpretation_rejected(make_case):
    bad = make_case()
    bad.pop("physical_interpretation")
    with pytest.raises(ValidationError):
        Case.model_validate(bad)


def test_physical_interpretation_requires_directionality(make_case):
    bad = make_case()
    bad["physical_interpretation"] = {
        "consistency_check": "consistent with model assumptions",
        "caveats": [],
    }
    with pytest.raises(ValidationError):
        Case.model_validate(bad)


def test_physical_interpretation_requires_consistency_check(make_case):
    bad = make_case()
    bad["physical_interpretation"] = {
        "directionality": "lower Kd implies tighter binding",
        "caveats": [],
    }
    with pytest.raises(ValidationError):
        Case.model_validate(bad)
