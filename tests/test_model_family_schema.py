"""Physics model-family schema and compatibility checks."""

from __future__ import annotations

import copy

import pytest
from pydantic import ValidationError

from biophysevo.schemas.case_schema import Case


def test_model_family_is_required(make_case):
    case = make_case()
    case["biophysical_model"].pop("model_family", None)
    with pytest.raises(ValidationError, match="model_family"):
        Case.model_validate(case)


def test_domain_incompatible_model_family_is_rejected(make_case):
    case = make_case()
    case["domain"] = "protein_ligand_binding"
    case["bridge_type"] = "binding_thermodynamics_to_binding_mechanism"
    case["biophysical_model"]["model_family"] = "enzyme_reaction_kinetics"
    with pytest.raises(ValidationError, match="not compatible"):
        Case.model_validate(case)


def test_secondary_model_families_must_not_duplicate_primary(make_case):
    case = make_case()
    primary = case["biophysical_model"]["model_family"]
    case["biophysical_model"]["secondary_model_families"] = [primary]
    with pytest.raises(ValidationError, match="must not include"):
        Case.model_validate(case)


def test_secondary_model_families_accept_valid_supporting_families(make_case):
    case = make_case()
    case["biophysical_model"]["secondary_model_families"] = [
        "conformational_allostery_energy_landscape"
    ]
    parsed = Case.model_validate(copy.deepcopy(case))
    assert parsed.biophysical_model.secondary_model_families == [
        "conformational_allostery_energy_landscape"
    ]
