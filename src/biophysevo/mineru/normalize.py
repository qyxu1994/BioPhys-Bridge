"""CLI: normalize MinerU API captures into the canonical parsed_docs layout.

The API capture script (`scripts/run_mineru_api.py`) writes one folder per PDF
under `data/intermediate/mineru_api/<doc>/` containing `payload.json` (+ `full.md`).
The extraction pipeline (`extract_candidates`) instead reads
`data/intermediate/parsed_docs/<doc>/{document.md, evidence_blocks.jsonl, ...}`.
This stage bridges the two by running `normalize_mineru_payload` over each capture.

Per-doc provenance (license/doi/pmcid/paper_title/source_url) is read from an
optional `--provenance` JSON keyed by doc_id and injected into
`parse_metadata.json` under `source_item`, which `extract_candidates` propagates
into `Case.source` (otherwise license defaults to "unknown").

    python -m biophysevo.mineru.normalize \
        --input-dir data/intermediate/mineru_api \
        --out-dir data/intermediate/parsed_docs \
        --provenance data/raw/provenance.json \
        --run-dir runs/<ts>_normalize --resume
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from biophysevo.utils.logging import get_logger
from biophysevo.utils.run_manager import (
    RunManager,
    add_common_run_flags,
    command_string,
    resolve_run_dir,
)

from .normalize_outputs import normalize_mineru_payload

LOG = get_logger("biophysevo.mineru.normalize")


def _load_provenance(path: Path | None) -> dict[str, dict]:
    if path is None:
        return {}
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        LOG.error("could not read provenance %s: %s", path, exc)
        return {}
    return data if isinstance(data, dict) else {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Normalize MinerU API payloads into parsed_docs layout."
    )
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument(
        "--provenance",
        type=Path,
        default=None,
        help="Optional JSON keyed by doc_id with license/doi/pmcid/... fields.",
    )
    add_common_run_flags(parser)
    args = parser.parse_args(argv)

    if not args.input_dir.exists():
        LOG.error("input-dir does not exist: %s", args.input_dir)
        return 2

    provenance = _load_provenance(args.provenance)

    run_dir = resolve_run_dir(args, "normalize")
    run = RunManager(
        run_dir,
        config={"input_dir": str(args.input_dir), "out_dir": str(args.out_dir)},
        command=command_string(),
    )
    ckpt = run.checkpoint_store("normalize")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    n_skip = 0
    for doc_dir in sorted(p for p in args.input_dir.iterdir() if p.is_dir()):
        payload_path = doc_dir / "payload.json"
        if not payload_path.is_file():
            continue
        doc_id = doc_dir.name
        if args.limit is not None and n + n_skip >= args.limit:
            break
        if args.resume and ckpt.is_done(doc_id):
            n_skip += 1
            continue
        try:
            payload = json.loads(payload_path.read_text())
            source_item = provenance.get(doc_id, {})
            normalize_mineru_payload(
                doc_id,
                payload,
                args.out_dir,
                parse_metadata={"source_item": source_item},
                include_text_blocks=True,
            )
            ckpt.mark_done(doc_id)
            run.manifest.write({"doc_id": doc_id, "status": "normalized"})
            n += 1
        except Exception as exc:  # noqa: BLE001
            LOG.error("normalize failed for %s: %s", doc_id, exc)
            run.manifest.write(
                {"doc_id": doc_id, "status": "failed", "error": str(exc)[:300]}
            )

    run.write_metrics({"normalized": n, "skipped": n_skip})
    run.close()
    ckpt.close()
    LOG.info("normalize done: normalized=%d skipped=%d", n, n_skip)
    return 0


if __name__ == "__main__":
    sys.exit(main())
