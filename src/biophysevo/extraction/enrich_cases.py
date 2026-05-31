"""CLI: enrich validated cases with reasoning trajectories + physics check.

    python -m biophysevo.extraction.enrich_cases \
        --input data/intermediate/cases_validated_real.jsonl \
        --out data/intermediate/cases_enriched.jsonl \
        --use-llm --model gpt-4o --run-dir runs/<ts>_enrich --resume

Writes the enriched (schema-valid) cases to --out and a parallel
<out>.consistency.jsonl with the deterministic physics-consistency result per case.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from biophysevo.physics.consistency import check_case
from biophysevo.utils.io import read_jsonl, safe_jsonl_writer
from biophysevo.utils.logging import get_logger
from biophysevo.utils.run_manager import (
    RunManager,
    add_common_run_flags,
    command_string,
    resolve_run_dir,
)

from . import enrich_case as enrich_case_mod

LOG = get_logger("biophysevo.extraction.enrich_cases")


def _is_quota_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "insufficient_quota" in text or "exceeded your current quota" in text


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Enrich cases with reasoning + physics check.")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--use-llm", action="store_true")
    p.add_argument("--model", default="gpt-4o")
    add_common_run_flags(p)
    args = p.parse_args(argv)

    run = RunManager(
        resolve_run_dir(args, "enrich"),
        config={"input": str(args.input), "out": str(args.out)},
        command=command_string(),
    )
    ckpt = run.checkpoint_store("enrich")
    cons_path = args.out.with_suffix(args.out.suffix + ".consistency.jsonl")
    args.out.parent.mkdir(parents=True, exist_ok=True)

    n = n_skip = 0
    with safe_jsonl_writer(args.out) as w, safe_jsonl_writer(cons_path) as cw:
        for i, case in enumerate(read_jsonl(args.input), start=1):
            if args.limit is not None and n + n_skip >= args.limit:
                break
            cid = case.get("case_id") or f"case_{i}"
            if args.resume and ckpt.is_done(cid):
                n_skip += 1
                continue
            try:
                enriched = enrich_case_mod.enrich_case(
                    case, enabled=args.use_llm, model=args.model
                )
                cons = check_case(enriched)
                w.write(enriched)
                cw.write({"case_id": cid, "physics_consistency": cons})
                ckpt.mark_done(cid)
                run.manifest.write(
                    {"case_id": cid, "status": "enriched",
                     "consistency": (cons or {}).get("status", "not_checked")}
                )
                n += 1
            except Exception as exc:  # noqa: BLE001 - keep batch resumable.
                if _is_quota_error(exc):
                    LOG.error("enrichment blocked by LLM quota for %s: %s", cid, exc)
                    run.manifest.write(
                        {"case_id": cid, "status": "blocked_quota", "error": str(exc)[:300]}
                    )
                    run.write_metrics({"enriched": n, "skipped": n_skip, "blocked_quota": True})
                    run.close()
                    ckpt.close()
                    return 2
                LOG.error("enrichment failed for %s: %s", cid, exc)
                run.manifest.write(
                    {"case_id": cid, "status": "failed", "error": str(exc)[:300]}
                )

    run.write_metrics({"enriched": n, "skipped": n_skip})
    run.close()
    ckpt.close()
    LOG.info("enrich_cases done: enriched=%d skipped=%d", n, n_skip)
    return 0


if __name__ == "__main__":
    sys.exit(main())
