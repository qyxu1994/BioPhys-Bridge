"""Schema tests for Biophys-Bridge / Sci-Evo cases."""

from __future__ import annotations

import copy

import pytest
from pydantic import ValidationError

from biophysevo.schemas.case_schema import Case, validate_cases


def test_sample_case_validates(sample_case_dict):
    case = Case.model_validate(sample_case_dict)
    assert case.case_id.startswith("biophysevo_")
    assert case.dataset_type == "Sci-Evo"
    assert case.dataset_family == "Biophys-Bridge"
    assert case.dataset_subtype == "Sci-Evo"


def test_rejects_wrong_dataset_family(make_case):
    bad = make_case(dataset_family="NotBiophys-Bridge")
    with pytest.raises(ValidationError):
        Case.model_validate(bad)


def test_rejects_wrong_dataset_subtype(make_case):
    bad = make_case(dataset_subtype="NotSci-Evo")
    with pytest.raises(ValidationError):
        Case.model_validate(bad)


def test_rejects_mixed_domain(make_case):
    bad = make_case(domain="mixed")
    with pytest.raises(ValidationError):
        Case.model_validate(bad)


def test_rejects_wrong_dataset_type(make_case):
    bad = make_case(dataset_type="Sci-Align")
    with pytest.raises(ValidationError):
        Case.model_validate(bad)


def test_rejects_missing_license(make_case):
    bad = make_case()
    bad["source"].pop("license")
    with pytest.raises(ValidationError):
        Case.model_validate(bad)


def test_rejects_quant_evidence_without_evidence_id(make_case):
    bad = make_case()
    bad["quantitative_evidence"][0].pop("evidence_id")
    with pytest.raises(ValidationError):
        Case.model_validate(bad)


def test_rejects_quant_evidence_with_unknown_evidence_id(make_case):
    bad = make_case()
    bad["quantitative_evidence"][0]["evidence_id"] = "ev_unknown"
    with pytest.raises(ValidationError):
        Case.model_validate(bad)


def test_failure_present_requires_evidence_or_inferred_flag(make_case):
    bad = make_case()
    bad["failure_or_revision"] = {
        "present": True,
        "description": "tried X, failed",
        "revision_decision": "try Y",
        "evidence_ids": [],
        "inferred_from_discussion": False,
    }
    with pytest.raises(ValidationError):
        Case.model_validate(bad)


def test_failure_present_with_inferred_flag_is_allowed(make_case):
    ok = make_case()
    ok["failure_or_revision"] = {
        "present": True,
        "description": "inferred from discussion",
        "revision_decision": "tweak buffer",
        "evidence_ids": [],
        "inferred_from_discussion": True,
    }
    Case.model_validate(ok)


def test_agent_tasks_is_a_nonempty_list(make_case):
    parsed = Case.model_validate(make_case())
    assert isinstance(parsed.agent_tasks, list) and len(parsed.agent_tasks) >= 1


def test_each_agent_task_requires_supporting_evidence(make_case):
    bad = make_case()
    bad["agent_tasks"][0]["supporting_evidence_ids"] = []
    with pytest.raises(ValidationError):
        Case.model_validate(bad)


def test_unique_case_ids_enforced(sample_case_dict):
    a = copy.deepcopy(sample_case_dict)
    b = copy.deepcopy(sample_case_dict)
    with pytest.raises(ValueError, match="Duplicate case_id"):
        validate_cases([a, b])


def test_case_id_format(make_case):
    bad = make_case(case_id="not allowed!")
    with pytest.raises(ValidationError):
        Case.model_validate(bad)


def test_quant_evidence_preserves_units(sample_case_dict):
    case = Case.model_validate(sample_case_dict)
    qe = case.quantitative_evidence[0]
    assert qe.unit and qe.normalized_unit
    assert qe.value > 0 and qe.normalized_value is not None
