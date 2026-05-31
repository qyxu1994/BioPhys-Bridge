"""Evidence-coverage checks on validated cases."""

from __future__ import annotations

from biophysevo.schemas.case_schema import Case


def evidence_coverage_ratio(case: Case) -> float:
    """Fraction of quantitative evidence + gold_answer claims with evidence_id."""
    total = 0
    grounded = 0
    for qe in case.quantitative_evidence:
        total += 1
        if qe.evidence_id:
            grounded += 1
    total += 1  # gold_answer(s) must cite at least one
    if any(t.supporting_evidence_ids for t in case.agent_tasks):
        grounded += 1
    if total == 0:
        return 1.0
    return grounded / total


def has_quantitative_evidence(case: Case) -> bool:
    return len(case.quantitative_evidence) > 0
