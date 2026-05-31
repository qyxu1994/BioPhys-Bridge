"""biophysical_model (the revision-v2 physical_model block) is required on every Case."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from biophysevo.schemas.case_schema import Case


def test_missing_biophysical_model_rejected(make_case):
    bad = make_case()
    bad.pop("biophysical_model")
    with pytest.raises(ValidationError):
        Case.model_validate(bad)


def test_biophysical_model_requires_model_name(make_case):
    bad = make_case()
    bad["biophysical_model"] = {
        "equation_latex": r"\Delta G = R T \ln K_d",
        "variables": {},
        "assumptions": [],
        "validity_conditions": [],
    }
    with pytest.raises(ValidationError):
        Case.model_validate(bad)


def test_biophysical_model_accepts_full_block(make_case):
    ok = make_case()
    ok["biophysical_model"] = {
        "model_name": "standard_binding_free_energy",
        "model_family": "binding_thermodynamics",
        "secondary_model_families": [],
        "equation_latex": r"\Delta G^\circ = R T \ln K_d",
        "variables": {"K_d": "dissociation constant"},
        "assumptions": ["equilibrium 1:1 binding"],
        "validity_conditions": ["no aggregation"],
    }
    Case.model_validate(ok)
