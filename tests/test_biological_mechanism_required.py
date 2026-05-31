"""biological_mechanism is required on every Case (revision-v2 L108-114)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from biophysevo.schemas.case_schema import Case


def test_missing_biological_mechanism_rejected(make_case):
    bad = make_case()
    bad.pop("biological_mechanism")
    with pytest.raises(ValidationError):
        Case.model_validate(bad)


def test_biological_mechanism_requires_mechanism_type(make_case):
    bad = make_case()
    bad["biological_mechanism"] = {
        "description": "binding into the orthosteric pocket",
    }
    with pytest.raises(ValidationError):
        Case.model_validate(bad)


def test_biological_mechanism_requires_description(make_case):
    bad = make_case()
    bad["biological_mechanism"] = {
        "mechanism_type": "protein_ligand_binding_mechanism",
    }
    with pytest.raises(ValidationError):
        Case.model_validate(bad)
