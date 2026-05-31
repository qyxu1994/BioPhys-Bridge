"""Direct tests for quality.validate_evidence."""

from __future__ import annotations

from biophysevo.quality.validate_evidence import (
    evidence_coverage_ratio,
    has_quantitative_evidence,
)
from biophysevo.schemas.case_schema import Case


def test_has_quantitative_evidence_true_on_sample(sample_case_dict):
    case = Case.model_validate(sample_case_dict)
    assert has_quantitative_evidence(case) is True


def test_has_quantitative_evidence_false_when_empty(make_case):
    raw = make_case()
    raw["quantitative_evidence"] = []
    case = Case.model_validate(raw)
    assert has_quantitative_evidence(case) is False


def test_evidence_coverage_full_when_grounded(sample_case_dict):
    """Sample case grounds all quantitative evidence + the gold answer."""
    case = Case.model_validate(sample_case_dict)
    assert evidence_coverage_ratio(case) == 1.0


def test_evidence_coverage_drops_with_ungrounded_metric(make_case, sample_case_dict):
    """An unevidenced metric lowers coverage below 1.0.

    Add a duplicate quantitative_evidence entry with a blank evidence_id; the
    schema validator requires referenced ids to resolve, so we bypass it by
    constructing the Case then mutating the in-memory list.
    """
    case = Case.model_validate(sample_case_dict)
    extra = case.quantitative_evidence[0].model_copy(update={"evidence_id": ""})
    case.quantitative_evidence.append(extra)
    # Now: original grounded + ungrounded extra + grounded gold_answer = 2/3.
    ratio = evidence_coverage_ratio(case)
    assert 0.0 < ratio < 1.0
