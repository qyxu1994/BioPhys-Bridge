"""CLI: build Sci-Evo cases from candidate extractions.

    python -m biophysevo.extraction.build_cases \
        --candidates data/intermediate/candidates.jsonl \
        --out data/intermediate/cases_draft.jsonl \
        --run-dir runs/<ts>_build_cases --resume [--use-llm]
"""

from __future__ import annotations

import argparse
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

from . import llm_fill
from .sci_evo_builder import build_case_from_candidate


LOG = get_logger("biophysevo.extraction.build_cases")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Sci-Evo cases.")
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Optional LLM-assisted structuring (opt-in, requires API key).",
    )
    parser.add_argument(
        "--case-id-prefix",
        default="biophysevo_",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="LLM model used when --use-llm is set.",
    )
    add_common_run_flags(parser)
    args = parser.parse_args(argv)

    run_dir = resolve_run_dir(args, "build_cases")
    run = RunManager(
        run_dir,
        config={
            "candidates": str(args.candidates),
            "out": str(args.out),
            "use_llm": args.use_llm,
        },
        command=command_string(),
    )
    ckpt = run.checkpoint_store("build")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    n_built = 0
    n_skip = 0
    n_drop = 0
    with safe_jsonl_writer(args.out) as writer:
        for i, cand in enumerate(read_jsonl(args.candidates), start=1):
            if args.limit is not None and i > args.limit:
                break
            doc_id = cand.get("doc_id") or f"doc_{i}"
            if args.resume and ckpt.is_done(doc_id):
                n_skip += 1
                continue
            case_id = f"{args.case_id_prefix}{i:06d}"
            try:
                llm_fields = None
                if args.use_llm:
                    llm_fields = llm_fill.extract_case_fields(
                        cand.get("evidence_blocks", []) or [],
                        enabled=True,
                        model=args.model,
                    )
                case = build_case_from_candidate(
                    cand,
                    case_id=case_id,
                    source={
                        "license": cand.get("license", "unknown"),
                        "mineru_parse_id": cand.get("doc_id"),
                        "paper_title": cand.get("paper_title"),
                        "doi": cand.get("doi"),
                        "pmcid": cand.get("pmcid"),
                    },
                    mineru_artifact_path=cand.get("mineru_artifact_path"),
                    llm_fields=llm_fields,
                )
            except Exception as exc:  # noqa: BLE001
                LOG.error("build failed for %s: %s", doc_id, exc)
                run.manifest.write(
                    {"doc_id": doc_id, "status": "failed", "error": str(exc)[:300]}
                )
                continue
            if case is None:
                n_drop += 1
                run.manifest.write({"doc_id": doc_id, "status": "dropped"})
                continue
            writer.write(case)
            ckpt.mark_done(doc_id)
            run.manifest.write({"doc_id": doc_id, "status": "built", "case_id": case_id})
            n_built += 1

    run.write_metrics({"built": n_built, "skipped": n_skip, "dropped": n_drop})
    run.close()
    ckpt.close()
    LOG.info("build_cases done: built=%d skipped=%d dropped=%d", n_built, n_skip, n_drop)
    return 0


if __name__ == "__main__":
    sys.exit(main())
