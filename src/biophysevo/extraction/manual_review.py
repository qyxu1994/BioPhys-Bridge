"""Build a manual review queue from validated cases (plan-v1 Stage 7)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from biophysevo.quality.scoring import per_case_score
from biophysevo.schemas.case_schema import Case
from biophysevo.utils.io import atomic_write_jsonl, read_jsonl


def _priority(case: Case) -> tuple[int, float]:
    """Higher priority first.

    Boosts cases with tables/formulas, with failure_or_revision, and with
    grounded quantitative evidence.
    """
    boost = 0
    if any(e.modality in {"table", "formula"} for e in case.evidence):
        boost += 1
    if case.failure_or_revision and case.failure_or_revision.present:
        boost += 1
    if case.quantitative_evidence:
        boost += 1
    return (boost, per_case_score(case))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the manual review queue.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/intermediate/manual_review_queue.jsonl"),
    )
    args = parser.parse_args(argv)

    raw = list(read_jsonl(args.input))
    cases: list[Case] = []
    for r in raw:
        try:
            cases.append(Case.model_validate(r))
        except Exception:
            continue

    ranked = sorted(cases, key=_priority, reverse=True)
    queue = [
        {
            "case_id": c.case_id,
            "review_status": "unreviewed",
            "priority_rank": i + 1,
            "score": per_case_score(c),
        }
        for i, c in enumerate(ranked)
    ]
    atomic_write_jsonl(args.out, queue)
    print(f"wrote {len(queue)} item(s) -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
