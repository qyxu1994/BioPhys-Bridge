"""CLI: regex-first candidate extraction from MinerU parsed docs.

    python -m biophysevo.extraction.extract_candidates \
        --parsed-dir data/intermediate/parsed_docs \
        --out data/intermediate/candidates.jsonl \
        --run-dir runs/<ts>_candidate_extraction --resume
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from biophysevo.utils.io import safe_jsonl_writer
from biophysevo.utils.logging import get_logger
from biophysevo.utils.run_manager import (
    RunManager,
    add_common_run_flags,
    command_string,
    resolve_run_dir,
)

from .entities import extract_entities
from .evidence import find_evidence_for_text, load_evidence_blocks
from .formulas import load_formulas_from_parsed_doc
from .measurements import find_measurements
from biophysevo.quality.validate_units import normalize


LOG = get_logger("biophysevo.extraction.extract_candidates")


def _read_source_item(doc_dir: Path) -> dict:
    """Pull the originating manifest item out of parse_metadata.json (if any)."""
    meta_path = doc_dir / "parse_metadata.json"
    if not meta_path.exists():
        return {}
    try:
        meta = json.loads(meta_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}
    return meta.get("source_item") or {}


def _process_doc(doc_dir: Path) -> dict:
    md_path = doc_dir / "document.md"
    text = md_path.read_text() if md_path.exists() else ""

    blocks = load_evidence_blocks(doc_dir)
    block_text = "\n\n".join((b.get("text") or "") for b in blocks)
    full_text = text + "\n\n" + block_text

    entities = extract_entities(full_text)
    measurements_raw = find_measurements(full_text)
    formulas = load_formulas_from_parsed_doc(doc_dir)

    measurements: list[dict] = []
    for m in measurements_raw:
        normalized = normalize(m.metric, m.value, m.unit)
        snippet = full_text[max(0, m.span[0] - 30): m.span[1] + 30]
        eid = find_evidence_for_text(
            full_text[m.span[0]: m.span[1]], blocks
        ) or find_evidence_for_text(snippet, blocks)
        if eid is None and blocks:
            eid = blocks[0]["evidence_id"]
        measurements.append(
            {
                "metric": m.metric,
                "value": m.value,
                "unit": m.unit,
                "normalized_value": normalized.normalized_value,
                "normalized_unit": normalized.normalized_unit,
                "evidence_id": eid,
                "snippet": snippet.strip(),
            }
        )

    source_item = _read_source_item(doc_dir)

    candidate = {
        "doc_id": doc_dir.name,
        "entities": entities,
        "measurements": measurements,
        "formulas": [{"latex": f.get("latex", "")} for f in formulas if f.get("latex")],
        "evidence_blocks": blocks,
    }
    # Propagate provenance from the source manifest so build_cases can populate
    # Source.license (and DOI/PMCID) instead of defaulting to "unknown".
    for key in ("license", "doi", "pmcid", "source_url", "paper_title"):
        if source_item.get(key) is not None:
            candidate[key] = source_item[key]
    return candidate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract candidate fields from parsed docs.")
    parser.add_argument("--parsed-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    add_common_run_flags(parser)
    args = parser.parse_args(argv)

    parsed_root = args.parsed_dir
    if not parsed_root.exists():
        LOG.error("parsed-dir does not exist: %s", parsed_root)
        return 2

    run_dir = resolve_run_dir(args, "candidate_extraction")
    run = RunManager(
        run_dir,
        config={"parsed_dir": str(parsed_root), "out": str(args.out)},
        command=command_string(),
    )
    ckpt = run.checkpoint_store("extract")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    n_skip = 0
    with safe_jsonl_writer(args.out) as writer:
        for doc_dir in sorted(p for p in parsed_root.iterdir() if p.is_dir()):
            if args.limit is not None and n + n_skip >= args.limit:
                break
            doc_id = doc_dir.name
            if args.resume and ckpt.is_done(doc_id):
                n_skip += 1
                continue
            try:
                payload = _process_doc(doc_dir)
                writer.write(payload)
                ckpt.mark_done(doc_id)
                run.manifest.write({"doc_id": doc_id, "status": "succeeded"})
                n += 1
            except Exception as exc:  # noqa: BLE001
                LOG.error("extraction failed for %s: %s", doc_id, exc)
                run.manifest.write(
                    {"doc_id": doc_id, "status": "failed", "error": str(exc)[:300]}
                )

    run.write_metrics({"succeeded": n, "skipped": n_skip})
    run.close()
    ckpt.close()
    LOG.info("extract_candidates done: succeeded=%d skipped=%d", n, n_skip)
    return 0


if __name__ == "__main__":
    sys.exit(main())
