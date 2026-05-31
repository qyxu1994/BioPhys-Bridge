"""Aggregate metrics for the quality report (plan-v1 Stage 8)."""

from __future__ import annotations

from typing import Any

from biophysevo.schemas.case_schema import Case

from .deduplicate import find_duplicate_case_ids
from .license_check import has_license
from .validate_evidence import evidence_coverage_ratio, has_quantitative_evidence


def _unit_normalization_ok(case: Case) -> bool:
    if not case.quantitative_evidence:
        return True
    return all(
        qe.normalized_value is not None and qe.normalized_unit is not None
        for qe in case.quantitative_evidence
    )


def _has_mineru_artifact(case: Case) -> bool:
    return any(e.mineru_artifact_path for e in case.evidence) or bool(
        case.source.mineru_parse_id
    )


def _sci_evo_completeness(case: Case) -> float:
    """Fraction of canonical Sci-Evo stages present in the trajectory."""
    expected = {
        "research_question",
        "hypothesis",
        "method_design",
        "quantitative_observation",
        "biophysical_interpretation",
        "failure_or_revision",
        "next_step",
    }
    present = {s.stage for s in case.sci_evo_trajectory}
    if not expected:
        return 1.0
    return len(present & expected) / len(expected)


def per_case_score(case: Case) -> float:
    """Mean of normalized 0-1 quality signals."""
    signals = [
        1.0,  # schema_valid (cases reaching here passed Pydantic)
        float(has_license(case)),
        float(has_quantitative_evidence(case)),
        float(_unit_normalization_ok(case)),
        float(_has_mineru_artifact(case)),
        evidence_coverage_ratio(case),
        _sci_evo_completeness(case),
    ]
    return sum(signals) / len(signals)


def aggregate_metrics(
    cases: list[Case],
    *,
    n_raw: int | None = None,
    n_schema_errors: int = 0,
    manual_pass: int | None = None,
) -> dict[str, Any]:
    n = len(cases)
    if n_raw is None:
        n_raw = n + n_schema_errors

    dups = find_duplicate_case_ids(cases)
    schema_valid_rate = (n / n_raw) if n_raw else 0.0
    quant_rate = (
        sum(1 for c in cases if has_quantitative_evidence(c)) / n if n else 0.0
    )
    unit_rate = (
        sum(1 for c in cases if _unit_normalization_ok(c)) / n if n else 0.0
    )
    license_rate = (
        sum(1 for c in cases if has_license(c)) / n if n else 0.0
    )
    mineru_rate = (
        sum(1 for c in cases if _has_mineru_artifact(c)) / n if n else 0.0
    )
    ev_cov = (
        sum(evidence_coverage_ratio(c) for c in cases) / n if n else 0.0
    )
    completeness = (
        sum(_sci_evo_completeness(c) for c in cases) / n if n else 0.0
    )
    duplicate_rate = (len(dups) / n) if n else 0.0

    manual_review_pass_rate = None
    if manual_pass is not None and n:
        manual_review_pass_rate = manual_pass / n

    return {
        "n_raw": n_raw,
        "n_valid": n,
        "schema_valid_rate": schema_valid_rate,
        "quantitative_evidence_rate": quant_rate,
        "unit_normalization_success_rate": unit_rate,
        "source_license_coverage": license_rate,
        "mineru_artifact_coverage": mineru_rate,
        "evidence_coverage_rate": ev_cov,
        "sci_evo_completeness_score": completeness,
        "duplicate_rate": duplicate_rate,
        "duplicate_case_ids": dups,
        "manual_review_pass_rate": manual_review_pass_rate,
    }
