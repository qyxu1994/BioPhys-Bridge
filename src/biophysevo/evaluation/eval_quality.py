"""Quality evaluation with smoke/dev/full modes and isolation guards.

    python -m biophysevo.evaluation.eval_quality \
        --input data/intermediate/cases_validated.jsonl \
        --mode {smoke,dev,full} \
        --run-dir runs/<ts>_quality_smoke --resume

Safeguards per plan-v1 section 7:
- full refuses to run if the output folder already exists.
- full refuses to run if duplicate case_ids are detected.
- full requires the input to schema-validate first.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from biophysevo.quality.deduplicate import find_duplicate_case_ids
from biophysevo.quality.scoring import aggregate_metrics, per_case_score
from biophysevo.quality.validate_schema import validate_each
from biophysevo.utils.io import read_jsonl, safe_jsonl_writer
from biophysevo.utils.logging import get_logger
from biophysevo.utils.run_manager import (
    RunManager,
    add_common_run_flags,
    command_string,
    resolve_run_dir,
)

LOG = get_logger("biophysevo.evaluation.eval_quality")

MODE_SAMPLE = {"smoke": 5, "dev": 30, "full": None}


def _resolve_output(mode: str, args: argparse.Namespace) -> Path:
    """Map mode -> output root. Enforces smoke/full isolation."""
    if mode == "full":
        return args.full_results_dir or Path("results/aggregate")
    return resolve_run_dir(args, f"quality_{mode}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Quality evaluation.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--mode", choices=["smoke", "dev", "full"], required=True)
    parser.add_argument(
        "--full-results-dir",
        type=Path,
        default=None,
        help="Override default results/aggregate/ output for --mode full.",
    )
    add_common_run_flags(parser)
    args = parser.parse_args(argv)

    raw = list(read_jsonl(args.input))
    if args.limit is not None:
        raw = raw[: args.limit]
    elif args.mode != "full":
        cap = MODE_SAMPLE[args.mode]
        if cap is not None:
            raw = raw[:cap]

    output_root = _resolve_output(args.mode, args)

    if args.mode == "full":
        if output_root.exists():
            print(
                f"full mode refuses to run: output dir already exists: {output_root}",
                file=sys.stderr,
            )
            return 2
        valid, errors = validate_each(raw)
        if errors:
            print(
                f"full mode refuses to run: {len(errors)} schema error(s) in input",
                file=sys.stderr,
            )
            return 2
        dups = find_duplicate_case_ids(valid)
        if dups:
            print(
                f"full mode refuses to run: duplicate case_ids: {dups}",
                file=sys.stderr,
            )
            return 2
        output_root.mkdir(parents=True, exist_ok=False)
        run = RunManager(
            output_root,
            config={"mode": "full", "input": str(args.input)},
            command=command_string(),
        )
    else:
        run = RunManager(
            output_root,
            config={"mode": args.mode, "input": str(args.input)},
            command=command_string(),
        )
        valid, errors = validate_each(raw)

    ckpt = run.checkpoint_store("eval")

    per_case_path = run.run_dir / "per_case.jsonl"
    n_done = 0
    with safe_jsonl_writer(per_case_path) as writer:
        for case in valid:
            if args.resume and ckpt.is_done(case.case_id):
                continue
            writer.write(
                {
                    "case_id": case.case_id,
                    "score": per_case_score(case),
                }
            )
            ckpt.mark_done(case.case_id)
            n_done += 1

    metrics = aggregate_metrics(
        valid,
        n_raw=len(raw),
        n_schema_errors=len(errors),
    )
    metrics["mode"] = args.mode
    metrics["evaluated_this_run"] = n_done

    run.write_metrics(metrics)

    if args.mode == "full":
        (Path(output_root) / "quality_metrics.json").write_text(
            json.dumps(metrics, indent=2, sort_keys=True)
        )

    run.close()
    ckpt.close()
    LOG.info("eval_quality (%s) done: %s", args.mode, metrics)
    return 0


if __name__ == "__main__":
    sys.exit(main())
