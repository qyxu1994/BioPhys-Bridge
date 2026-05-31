"""CLI: parse PDFs listed in a manifest using MinerU (API / local / dry-run).

    python -m biophysevo.mineru.parse \
        --manifest data/raw/source_manifest.jsonl \
        --config configs/mineru.yaml \
        --run-dir runs/<timestamp>_mineru_parse \
        --resume [--dry-run] [--limit N]
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml

from biophysevo.utils.io import read_jsonl
from biophysevo.utils.logging import get_logger
from biophysevo.utils.run_manager import (
    RunManager,
    add_common_run_flags,
    command_string,
    resolve_run_dir,
)

from .client import (
    MinerUAgentClient,
    MinerUAgentConfig,
    MinerUClient,
    MinerUClientConfig,
)
from .local_runner import LocalMinerURunner, LocalRunnerConfig
from .normalize_outputs import dry_run_payload, normalize_mineru_payload


LOG = get_logger("biophysevo.mineru.parse")


def _load_config(path: Path | None) -> dict:
    if path is None:
        return {}
    with path.open() as fh:
        return yaml.safe_load(fh) or {}


def _parse_one(mode: str, pdf_path: Path, doc_id: str, out_root: Path, cfg: dict) -> dict:
    if mode == "dry-run":
        return dry_run_payload(doc_id)
    if mode == "api":
        api_cfg = cfg.get("api", {}) or {}
        client = MinerUClient(
            MinerUClientConfig(
                base_url=api_cfg.get("base_url", MinerUClientConfig.base_url),
                timeout_seconds=api_cfg.get(
                    "timeout_seconds", MinerUClientConfig.timeout_seconds
                ),
            )
        )
        return client.parse_pdf(pdf_path)
    if mode == "agent":
        agent_cfg = cfg.get("agent", {}) or {}
        defaults = MinerUAgentConfig()
        client = MinerUAgentClient(
            MinerUAgentConfig(
                base_url=agent_cfg.get("base_url", defaults.base_url),
                timeout_seconds=agent_cfg.get("timeout_seconds", defaults.timeout_seconds),
                language=agent_cfg.get("language", defaults.language),
                enable_table=agent_cfg.get("enable_table", defaults.enable_table),
                enable_formula=agent_cfg.get("enable_formula", defaults.enable_formula),
                is_ocr=agent_cfg.get("is_ocr", defaults.is_ocr),
                page_range=agent_cfg.get("page_range", defaults.page_range),
                poll_interval_seconds=agent_cfg.get(
                    "poll_interval_seconds", defaults.poll_interval_seconds
                ),
                max_poll_attempts=agent_cfg.get(
                    "max_poll_attempts", defaults.max_poll_attempts
                ),
            )
        )
        return client.parse_pdf(pdf_path)
    if mode == "local":
        local_cfg = cfg.get("local", {}) or {}
        runner = LocalMinerURunner(
            LocalRunnerConfig(
                cli=local_cfg.get("cli", "mineru"),
                extra_args=local_cfg.get("extra_args") or [],
            )
        )
        return runner.parse_pdf(pdf_path, out_root / doc_id / "_local_tmp")
    raise ValueError(f"unknown mineru mode: {mode!r}")


def _download_pdf(source_url: str, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(source_url, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        with out_path.open("wb") as fh:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    fh.write(chunk)
    return out_path


def _pdf_path_for_item(item: dict, *, download_dir: Path) -> Path | None:
    pdf_path = item.get("pdf_path")
    if pdf_path:
        return Path(pdf_path)
    source_url = item.get("source_url")
    if not source_url:
        return None
    parsed = urlparse(str(source_url))
    suffix = Path(parsed.path).suffix
    if suffix.lower() != ".pdf":
        suffix = ".pdf"
    doc_id = item.get("doc_id") or item.get("id") or "paper"
    return _download_pdf(str(source_url), download_dir / f"{doc_id}{suffix}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Parse PDFs via MinerU.")
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="JSONL of items with at least {doc_id, pdf_path}.",
    )
    parser.add_argument("--config", type=Path, default=Path("configs/mineru.yaml"))
    parser.add_argument(
        "--mode",
        choices=["api", "agent", "local", "dry-run"],
        default=None,
        help="Override config 'mode'.",
    )
    parser.add_argument(
        "--parsed-dir",
        type=Path,
        default=None,
        help="Override config outputs.parsed_dir.",
    )
    add_common_run_flags(parser)
    args = parser.parse_args(argv)

    cfg = _load_config(args.config)
    mode = args.mode or cfg.get("mode", "dry-run")
    if args.dry_run:
        mode = "dry-run"
    out_root = args.parsed_dir or Path((cfg.get("outputs") or {}).get(
        "parsed_dir", "data/intermediate/parsed_docs"
    ))
    out_root.mkdir(parents=True, exist_ok=True)

    run_dir = resolve_run_dir(args, "mineru_parse")
    run = RunManager(
        run_dir,
        config={"mode": mode, "manifest": str(args.manifest)},
        command=command_string(),
    )
    ckpt = run.checkpoint_store("parse")
    download_dir = run_dir / "downloads"

    n_done = 0
    n_skip = 0
    n_fail = 0
    n_seen = 0
    for item in read_jsonl(args.manifest):
        if args.limit is not None and n_seen >= args.limit:
            break
        n_seen += 1
        doc_id = item.get("doc_id") or item.get("id")
        if not doc_id:
            LOG.warning("skipping item without doc_id: %s", item)
            continue
        if args.resume and ckpt.is_done(doc_id):
            n_skip += 1
            run.manifest.write({"doc_id": doc_id, "status": "skipped"})
            continue

        run.manifest.write({"doc_id": doc_id, "status": "running"})
        try:
            if mode == "dry-run":
                pdf = Path("")
            else:
                pdf = _pdf_path_for_item(item, download_dir=download_dir)
                if pdf is None:
                    raise ValueError(
                        "manifest item needs pdf_path or source_url for non-dry-run parsing"
                    )
            payload = _parse_one(mode, pdf, doc_id, out_root, cfg)
            normalize_mineru_payload(
                doc_id,
                payload,
                out_root,
                parse_metadata={"mode": mode, "source_item": item},
            )
            ckpt.mark_done(doc_id, status="succeeded")
            run.manifest.write({"doc_id": doc_id, "status": "succeeded"})
            n_done += 1
        except Exception as exc:  # noqa: BLE001 - one bad doc must not abort the run
            LOG.error("parse failed for %s: %s", doc_id, exc)
            run.manifest.write(
                {"doc_id": doc_id, "status": "failed", "error": str(exc)[:300]}
            )
            n_fail += 1

    metrics = {
        "mode": mode,
        "seen": n_seen,
        "succeeded": n_done,
        "skipped": n_skip,
        "failed": n_fail,
    }
    run.write_metrics(metrics)
    run.close()
    ckpt.close()
    LOG.info("mineru.parse done: %s", metrics)
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
