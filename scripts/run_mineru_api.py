#!/usr/bin/env python3
"""Standalone MinerU v4 API parse utility.

Why this exists: the MinerU API gateway (mineru.net) and its presigned upload
storage endpoints may need to be reachable from the same shell where the parse
is launched. Run this from an environment with outbound access to both the
MinerU API and object-storage upload endpoints.

It reuses the repo's tested `MinerUClient` (the real v4 async flow:
POST /file-urls/batch -> PUT presigned URL -> poll extract-results -> download
ZIP -> parse content_list + markdown), so output matches the pipeline exactly.

Usage (from repo root, with the venv that has `pip install -e .`):

    # token in .env (MINERU_API_KEY=...) is loaded automatically
    python scripts/run_mineru_api.py                       # all PDFs in sample-papers/
    python scripts/run_mineru_api.py sample-papers/BPB0001*.pdf   # specific file(s)
    python scripts/run_mineru_api.py --out-dir /tmp/mineru_out    # custom output dir

Output: one folder per PDF under --out-dir (default data/intermediate/mineru_api/),
each containing `full.md` and `payload.json` (markdown + structured json + tables/
formulas/figures).
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
from glob import glob
from pathlib import Path
from urllib.parse import urlparse

# --- make the repo package importable when run as a plain script -------------
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from dotenv import load_dotenv  # python-dotenv is a dev dependency
    load_dotenv(REPO_ROOT / ".env")
except Exception:  # noqa: BLE001 - dotenv is optional; env may already be set
    pass

from biophysevo.mineru.client import (  # noqa: E402
    MinerUAPIError,
    MinerUClient,
    MinerUClientConfig,
)

OSS_HOST = "mineru.oss-cn-shanghai.aliyuncs.com"


def _preflight(host: str = OSS_HOST, port: int = 443, timeout: float = 8.0) -> bool:
    """Confirm we can actually open a TCP connection to the OSS upload host."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError as exc:
        print(f"[preflight] CANNOT reach {host}:{port} -> {exc}")
        print("[preflight] Use a network environment that can reach the "
              "MinerU upload storage endpoint and re-run.")
        return False


def _resolve_pdfs(patterns: list[str]) -> list[Path]:
    if not patterns:
        patterns = [str(REPO_ROOT / "sample-papers" / "*.pdf")]
    paths: list[Path] = []
    for pat in patterns:
        paths.extend(Path(p) for p in sorted(glob(pat)))
    return [p for p in paths if p.suffix.lower() == ".pdf"]


def _already_parsed(doc_dir: Path) -> bool:
    """True if doc_dir holds a complete prior parse (valid payload.json with markdown).

    A partial/corrupt payload.json (missing, empty, unparseable, or no markdown)
    returns False so the PDF is re-parsed rather than silently skipped.
    """
    payload_path = doc_dir / "payload.json"
    if not payload_path.is_file() or payload_path.stat().st_size == 0:
        return False
    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return isinstance(payload, dict) and bool(payload.get("markdown"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdfs", nargs="*", help="PDF paths or globs (default: sample-papers/*.pdf)")
    ap.add_argument("--out-dir", type=Path,
                    default=REPO_ROOT / "data" / "intermediate" / "mineru_api")
    ap.add_argument("--language", default="en")
    ap.add_argument("--skip-preflight", action="store_true",
                    help="Skip the TCP reachability check (not recommended).")
    ap.add_argument("--force", action="store_true",
                    help="Re-parse PDFs even if a valid prior parse already exists "
                         "(default: skip already-parsed PDFs).")
    args = ap.parse_args(argv)

    client = MinerUClient(MinerUClientConfig(language=args.language))
    if not client.has_credentials:
        print("ERROR: MINERU_API_KEY is not set. Put it in .env or export it.")
        return 2

    if not args.skip_preflight and not _preflight():
        return 3

    pdfs = _resolve_pdfs(args.pdfs)
    if not pdfs:
        print("ERROR: no PDFs matched.")
        return 2
    print(f"Parsing {len(pdfs)} PDF(s) via MinerU v4 -> {args.out_dir}\n")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    n_ok = n_fail = n_skip = 0
    for pdf in pdfs:
        stem = pdf.stem.split()[0] or pdf.stem  # e.g. "BPB0001"
        doc_dir = args.out_dir / stem
        print(f"--- {pdf.name}")
        if not args.force and _already_parsed(doc_dir):
            print(f"    SKIP: already parsed -> {doc_dir} (use --force to re-parse)\n")
            n_skip += 1
            continue
        try:
            payload = client.parse_pdf(pdf)
        except (MinerUAPIError, OSError) as exc:
            print(f"    FAILED: {exc}\n")
            n_fail += 1
            continue
        doc_dir.mkdir(parents=True, exist_ok=True)
        (doc_dir / "full.md").write_text(payload.get("markdown", ""), encoding="utf-8")
        (doc_dir / "payload.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        md_len = len(payload.get("markdown", ""))
        n_tab = len(payload.get("tables", []))
        n_fig = len(payload.get("figures", []))
        n_eq = len(payload.get("formulas", []))
        print(f"    OK: markdown={md_len} chars, tables={n_tab}, "
              f"figures={n_fig}, formulas={n_eq} -> {doc_dir}\n")
        n_ok += 1

    print(f"Done: {n_ok} succeeded, {n_skip} skipped (already parsed), "
          f"{n_fail} failed.")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
