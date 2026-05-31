"""CLI: full validation pass with aggregate report.

    python -m biophysevo.quality.validate_cases \
        --input data/intermediate/cases_draft.jsonl \
        --out data/intermediate/cases_validated.jsonl \
        --report results/aggregate/validation_report.json \
        --run-dir runs/<ts>_validation
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from biophysevo.utils.io import read_jsonl, safe_jsonl_writer
from biophysevo.utils.logging import get_logger
from biophysevo.utils.run_manager import (
    RunManager,
    add_common_run_flags,
    command_string,
    resolve_run_dir,
)

from .deduplicate import find_duplicate_case_ids
from .scoring import aggregate_metrics, per_case_score
from .validate_schema import validate_each


LOG = get_logger("biophysevo.quality.validate_cases")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate cases and write a report.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument(
        "--fail-on-duplicate-case-ids",
        action="store_true",
        default=True,
    )
    add_common_run_flags(parser)
    args = parser.parse_args(argv)

    run_dir = resolve_run_dir(args, "validation")
    run = RunManager(
        run_dir,
        config={
            "input": str(args.input),
            "out": str(args.out),
            "report": str(args.report),
        },
        command=command_string(),
    )

    raw = list(read_jsonl(args.input))
    valid, errors = validate_each(raw)

    dups = find_duplicate_case_ids(valid)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    with safe_jsonl_writer(args.out) as writer:
        for c in valid:
            payload = json.loads(c.model_dump_json())
            payload["quality"]["score"] = per_case_score(c)
            writer.write(payload)

    metrics = aggregate_metrics(valid, n_raw=len(raw), n_schema_errors=len(errors))
    metrics["schema_errors"] = [
        {"index": e["index"], "case_id": e["case_id"], "error": e["error"][:500]}
        for e in errors[:50]
    ]
    args.report.write_text(json.dumps(metrics, indent=2, sort_keys=True))

    run.write_metrics(metrics)
    run.close()

    LOG.info(
        "validate_cases done: valid=%d errors=%d duplicates=%d",
        len(valid),
        len(errors),
        len(dups),
    )
    if args.fail_on_duplicate_case_ids and dups:
        print(f"duplicate case_ids detected: {dups}", file=sys.stderr)
        return 1
    if errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
