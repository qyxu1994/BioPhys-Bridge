"""Duplicate detection for case_id and near-duplicate evidence."""

from __future__ import annotations

from collections import Counter

from biophysevo.schemas.case_schema import Case


def find_duplicate_case_ids(cases: list[Case]) -> list[str]:
    counts = Counter(c.case_id for c in cases)
    return [cid for cid, n in counts.items() if n > 1]
