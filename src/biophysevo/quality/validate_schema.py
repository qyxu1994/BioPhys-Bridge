"""Validate a list of raw case dicts against the Pydantic schema."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from biophysevo.schemas.case_schema import Case


def validate_each(raw_cases: list[dict[str, Any]]) -> tuple[list[Case], list[dict]]:
    """Return (valid_cases, errors). One pass; collects all errors.

    Each error entry: {"index": int, "case_id": str|None, "error": str}.
    """
    valid: list[Case] = []
    errors: list[dict] = []
    for i, raw in enumerate(raw_cases):
        try:
            valid.append(Case.model_validate(raw))
        except ValidationError as exc:
            errors.append(
                {
                    "index": i,
                    "case_id": raw.get("case_id"),
                    "error": str(exc),
                }
            )
    return valid, errors
