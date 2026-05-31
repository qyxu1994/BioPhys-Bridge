"""MinerU wrapper tests (mocked; no live API calls)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import io
import zipfile

import biophysevo.mineru.client as client_mod
from biophysevo.mineru.client import (
    MinerUAgentClient,
    MinerUAgentConfig,
    MinerUAPIError,
    MinerUClient,
    MinerUClientConfig,
)
from biophysevo.mineru import local_runner as local_runner_mod
from biophysevo.mineru.local_runner import LocalMinerURunner, LocalRunnerConfig, LocalRunnerError
from biophysevo.mineru.normalize_outputs import (
    dry_run_payload,
    mineru_content_list_to_payload,
    normalize_mineru_payload,
)
from biophysevo.mineru import parse as parse_mod
from biophysevo.mineru.parse import _pdf_path_for_item, main as parse_main


def test_client_requires_api_key(monkeypatch, tmp_path):
    monkeypatch.delenv("MINERU_API_KEY", raising=False)
    client = MinerUClient()
    assert not client.has_credentials
    pdf = tmp_path / "fake.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    with pytest.raises(MinerUAPIError):
        client.parse_pdf(pdf)


class _FakeResp:
    """Minimal stand-in for a ``requests`` Response."""

    def __init__(self, *, status_code=200, payload=None, content=b"", text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.content = content
        self.text = text

    def json(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"status {self.status_code}")

    def iter_content(self, chunk_size=1):
        yield self.content


def _result_zip_bytes() -> bytes:
    """A MinerU result ZIP: a markdown file + a *_content_list.json."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("full.md", "# Results\n\nKd = 120 nM.\n")
        zf.writestr(
            "paper_content_list.json",
            json.dumps(
                [
                    {
                        "type": "table",
                        "table_body": "<table><tr><td>Kd = 120 nM</td></tr></table>",
                        "table_caption": ["Table 1."],
                        "page_idx": 0,
                    },
                    {"type": "equation", "text": "$$\\Delta G = R T \\ln K_d$$", "page_idx": 0},
                ]
            ),
        )
    return buf.getvalue()


def test_client_v4_full_flow(monkeypatch, tmp_path):
    """Real MinerU v4 flow: request URLs -> upload -> poll -> download zip -> payload."""
    monkeypatch.setenv("MINERU_API_KEY", "test")
    client = MinerUClient(
        MinerUClientConfig(base_url="http://test", poll_interval_seconds=0)
    )
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 body")

    uploaded: dict[str, bytes] = {}
    polls = {"n": 0}

    def fake_post(url, headers=None, json=None, timeout=None):
        assert url == "http://test/file-urls/batch"
        assert headers["Authorization"] == "Bearer test"
        assert json["files"][0]["name"] == "paper.pdf"
        return _FakeResp(
            payload={"code": 0, "data": {"batch_id": "B1", "file_urls": ["http://up/put1"]}}
        )

    def fake_put(url, data=None, timeout=None):
        assert url == "http://up/put1"
        uploaded["bytes"] = data.read() if hasattr(data, "read") else data
        return _FakeResp(status_code=200)

    def fake_get(url, headers=None, timeout=None):
        if url == "http://test/extract-results/batch/B1":
            polls["n"] += 1
            state = "running" if polls["n"] < 2 else "done"
            return _FakeResp(
                payload={
                    "code": 0,
                    "data": {
                        "extract_result": [
                            {
                                "file_name": "paper.pdf",
                                "state": state,
                                "full_zip_url": "http://zip/r.zip" if state == "done" else "",
                            }
                        ]
                    },
                }
            )
        if url == "http://zip/r.zip":
            return _FakeResp(content=_result_zip_bytes())
        raise AssertionError(f"unexpected GET {url}")

    monkeypatch.setattr(client_mod.requests, "post", fake_post)
    monkeypatch.setattr(client_mod.requests, "put", fake_put)
    monkeypatch.setattr(client_mod.requests, "get", fake_get)

    payload = client.parse_pdf(pdf)

    assert uploaded["bytes"][:5] == b"%PDF-"
    assert polls["n"] >= 2  # polled until state == done
    assert "Kd = 120 nM" in payload["markdown"]
    assert len(payload["tables"]) == 1
    assert payload["tables"][0]["caption"] == "Table 1."
    assert len(payload["formulas"]) == 1
    assert payload["formulas"][0]["latex"] == r"\Delta G = R T \ln K_d"


def test_parse_manifest_source_url_downloads_pdf(monkeypatch, tmp_path):
    def fake_get(url, stream=None, timeout=None):
        assert url == "https://example.org/paper.pdf"
        assert stream is True
        return _FakeResp(content=b"%PDF-1.4 downloaded")

    monkeypatch.setattr(parse_mod.requests, "get", fake_get)
    pdf = _pdf_path_for_item(
        {"doc_id": "doc1", "pdf_path": None, "source_url": "https://example.org/paper.pdf"},
        download_dir=tmp_path,
    )
    assert pdf == tmp_path / "doc1.pdf"
    assert pdf.read_bytes().startswith(b"%PDF-")


def test_client_v4_error_code_raises(monkeypatch, tmp_path):
    """A non-zero API ``code`` surfaces as MinerUAPIError."""
    monkeypatch.setenv("MINERU_API_KEY", "test")
    client = MinerUClient(MinerUClientConfig(base_url="http://test", poll_interval_seconds=0))
    pdf = tmp_path / "p.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(
        client_mod.requests,
        "post",
        lambda *a, **k: _FakeResp(payload={"code": -1, "msg": "bad key"}, text="bad key"),
    )
    with pytest.raises(MinerUAPIError, match="bad key"):
        client.parse_pdf(pdf)


def test_client_v4_parse_failed_state_raises(monkeypatch, tmp_path):
    """A terminal ``failed`` state from the poll endpoint raises."""
    monkeypatch.setenv("MINERU_API_KEY", "test")
    client = MinerUClient(MinerUClientConfig(base_url="http://test", poll_interval_seconds=0))
    pdf = tmp_path / "p.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(
        client_mod.requests,
        "post",
        lambda *a, **k: _FakeResp(
            payload={"code": 0, "data": {"batch_id": "B9", "file_urls": ["http://up/x"]}}
        ),
    )
    monkeypatch.setattr(client_mod.requests, "put", lambda *a, **k: _FakeResp(status_code=200))
    monkeypatch.setattr(
        client_mod.requests,
        "get",
        lambda *a, **k: _FakeResp(
            payload={
                "code": 0,
                "data": {
                    "extract_result": [
                        {"file_name": "p.pdf", "state": "failed", "err_msg": "ocr boom"}
                    ]
                },
            }
        ),
    )
    with pytest.raises(MinerUAPIError, match="ocr boom"):
        client.parse_pdf(pdf)


def test_agent_client_full_flow(monkeypatch, tmp_path):
    """Token-free Agent API: POST file -> PUT upload -> poll -> fetch markdown."""
    client = MinerUAgentClient(
        MinerUAgentConfig(base_url="http://test/agent", poll_interval_seconds=0)
    )
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 body")

    uploaded: dict[str, bytes] = {}
    polls = {"n": 0}

    def fake_post(url, headers=None, json=None, timeout=None):
        assert url == "http://test/agent/parse/file"
        assert "Authorization" not in (headers or {})  # token-free
        assert json["file_name"] == "paper.pdf"
        return _FakeResp(
            payload={"code": 0, "data": {"task_id": "T1", "file_url": "http://oss/put1"}}
        )

    def fake_put(url, data=None, timeout=None):
        assert url == "http://oss/put1"
        uploaded["bytes"] = data.read() if hasattr(data, "read") else data
        return _FakeResp(status_code=200)

    def fake_get(url, headers=None, timeout=None):
        if url == "http://test/agent/parse/T1":
            polls["n"] += 1
            state = "running" if polls["n"] < 2 else "done"
            return _FakeResp(
                payload={
                    "code": 0,
                    "data": {
                        "task_id": "T1",
                        "state": state,
                        "markdown_url": "http://cdn/full.md" if state == "done" else "",
                    },
                }
            )
        if url == "http://cdn/full.md":
            return _FakeResp(text="# Results\n\nKd = 120 nM.\n")
        raise AssertionError(f"unexpected GET {url}")

    monkeypatch.setattr(client_mod.requests, "post", fake_post)
    monkeypatch.setattr(client_mod.requests, "put", fake_put)
    monkeypatch.setattr(client_mod.requests, "get", fake_get)

    payload = client.parse_pdf(pdf)

    assert uploaded["bytes"][:5] == b"%PDF-"
    assert polls["n"] >= 2
    assert "Kd = 120 nM" in payload["markdown"]
    # Agent API is markdown-only: structured lists are present but empty.
    assert payload["tables"] == []
    assert payload["formulas"] == []
    assert payload["figures"] == []


def test_agent_client_failed_state_raises(monkeypatch, tmp_path):
    client = MinerUAgentClient(
        MinerUAgentConfig(base_url="http://test/agent", poll_interval_seconds=0)
    )
    pdf = tmp_path / "p.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(
        client_mod.requests,
        "post",
        lambda *a, **k: _FakeResp(
            payload={"code": 0, "data": {"task_id": "T2", "file_url": "http://oss/x"}}
        ),
    )
    monkeypatch.setattr(client_mod.requests, "put", lambda *a, **k: _FakeResp(status_code=200))
    monkeypatch.setattr(
        client_mod.requests,
        "get",
        lambda *a, **k: _FakeResp(
            payload={"code": 0, "data": {"task_id": "T2", "state": "failed", "err_msg": "boom"}}
        ),
    )
    with pytest.raises(MinerUAPIError, match="boom"):
        client.parse_pdf(pdf)


def test_local_runner_unavailable(monkeypatch, tmp_path):
    runner = LocalMinerURunner(LocalRunnerConfig(cli="definitely-not-a-real-binary"))
    assert not runner.is_available
    with pytest.raises(LocalRunnerError):
        runner.parse_pdf(tmp_path / "x.pdf", tmp_path)


def test_normalize_writes_layout(tmp_path):
    payload = dry_run_payload("docA")
    out = normalize_mineru_payload("docA", payload, tmp_path)
    assert (out / "document.md").exists()
    assert (out / "document.json").exists()
    assert (out / "tables.jsonl").exists()
    assert (out / "formulas.jsonl").exists()
    assert (out / "figures.jsonl").exists()
    assert (out / "evidence_blocks.jsonl").exists()
    assert (out / "parse_metadata.json").exists()

    meta = json.loads((out / "parse_metadata.json").read_text())
    assert meta["doc_id"] == "docA"
    assert meta["tables"] >= 1
    assert meta["evidence_blocks"] >= 1


def test_content_list_adapter_maps_blocks():
    """Real MinerU content_list blocks adapt into the canonical payload shape."""
    content_list = [
        {"type": "title", "text": "Results", "page_idx": 0},
        {"type": "text", "text": "We measured binding.", "page_idx": 0},
        {
            "type": "table",
            "table_body": "<table><tr><td>Kd = 120 nM</td></tr></table>",
            "table_caption": ["Table 1.", "Binding affinities."],
            "page_idx": 0,
        },
        {"type": "equation", "text": "$$\\Delta G = R T \\ln K_d$$", "page_idx": 1},
        {"type": "image", "img_caption": ["Figure 1.", "ITC isotherm."], "page_idx": 2},
    ]
    payload = mineru_content_list_to_payload(content_list, markdown="# Results\n")

    assert payload["markdown"] == "# Results\n"
    assert len(payload["tables"]) == 1
    assert payload["tables"][0]["page"] == 1  # page_idx 0 -> page 1
    assert payload["tables"][0]["caption"] == "Table 1. Binding affinities."
    assert "Kd = 120 nM" in payload["tables"][0]["text"]
    assert len(payload["formulas"]) == 1
    assert payload["formulas"][0]["latex"] == r"\Delta G = R T \ln K_d"  # $$ stripped
    assert payload["formulas"][0]["page"] == 2
    assert len(payload["figures"]) == 1
    assert payload["figures"][0]["caption"] == "Figure 1. ITC isotherm."
    assert payload["figures"][0]["page"] == 3

    # The adapted payload must be consumable by the normalizer.
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        out = normalize_mineru_payload("docX", payload, td)
        blocks = [
            json.loads(line)
            for line in (out / "evidence_blocks.jsonl").read_text().splitlines()
            if line.strip()
        ]
    modalities = {b["modality"] for b in blocks}
    assert modalities == {"table", "formula", "figure"}
    ids = {b["evidence_id"] for b in blocks}
    assert any(i.startswith("ev_t") for i in ids)
    assert any(i.startswith("ev_f") for i in ids)
    assert any(i.startswith("ev_g") for i in ids)


def test_local_runner_parses_real_layout(tmp_path, monkeypatch):
    """Runner invokes the CLI and adapts a realistic MinerU output tree."""
    monkeypatch.setattr(local_runner_mod.shutil, "which", lambda _cli: "/usr/bin/mineru")

    def fake_run(cmd, capture_output, text):
        # cmd == ["mineru", "-p", <pdf>, "-o", <out_dir>]
        out_dir = Path(cmd[cmd.index("-o") + 1])
        auto = out_dir / "paper" / "auto"
        auto.mkdir(parents=True, exist_ok=True)
        (auto / "paper.md").write_text("# Paper\n\nKd = 120 nM.\n")
        (auto / "paper_content_list.json").write_text(
            json.dumps(
                [
                    {
                        "type": "table",
                        "table_body": "<table><tr><td>Kd = 120 nM</td></tr></table>",
                        "table_caption": ["Table 1."],
                        "page_idx": 0,
                    },
                    {"type": "equation", "text": "$$\\Delta G = R T \\ln K_d$$", "page_idx": 0},
                ]
            )
        )

        class _Completed:
            returncode = 0
            stderr = ""

        return _Completed()

    monkeypatch.setattr(local_runner_mod.subprocess, "run", fake_run)

    runner = LocalMinerURunner(LocalRunnerConfig(cli="mineru"))
    assert runner.is_available
    payload = runner.parse_pdf(tmp_path / "paper.pdf", tmp_path / "out")

    assert "Kd = 120 nM" in payload["markdown"]
    assert len(payload["tables"]) == 1
    assert payload["tables"][0]["caption"] == "Table 1."
    assert len(payload["formulas"]) == 1
    assert payload["formulas"][0]["latex"] == r"\Delta G = R T \ln K_d"


def test_local_runner_missing_content_list(tmp_path, monkeypatch):
    """A CLI run that emits no content_list raises a clear error."""
    monkeypatch.setattr(local_runner_mod.shutil, "which", lambda _cli: "/usr/bin/mineru")

    def fake_run(cmd, capture_output, text):
        class _Completed:
            returncode = 0
            stderr = ""

        return _Completed()

    monkeypatch.setattr(local_runner_mod.subprocess, "run", fake_run)
    runner = LocalMinerURunner(LocalRunnerConfig(cli="mineru"))
    with pytest.raises(LocalRunnerError, match="no \\*_content_list.json"):
        runner.parse_pdf(tmp_path / "paper.pdf", tmp_path / "out")


def test_parse_cli_dry_run(tmp_path, monkeypatch):
    """End-to-end CLI run in dry-run mode produces parsed_docs + checkpoints."""
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        json.dumps({"doc_id": "doc1", "pdf_path": "x.pdf"}) + "\n"
        + json.dumps({"doc_id": "doc2", "pdf_path": "y.pdf"}) + "\n"
    )
    cfg = tmp_path / "mineru.yaml"
    cfg.write_text(
        "mode: dry-run\n"
        f"outputs:\n  parsed_dir: {tmp_path}/parsed_docs\n"
    )
    run_dir = tmp_path / "runs" / "test"

    rc = parse_main([
        "--manifest", str(manifest),
        "--config", str(cfg),
        "--run-dir", str(run_dir),
        "--dry-run",
    ])
    assert rc == 0
    assert (Path(tmp_path) / "parsed_docs" / "doc1" / "document.md").exists()
    assert (Path(tmp_path) / "parsed_docs" / "doc2" / "evidence_blocks.jsonl").exists()
    assert (run_dir / "metrics.json").exists()
    assert (run_dir / "checkpoints" / "parse.jsonl").exists()


def test_parse_cli_agent_mode(tmp_path, monkeypatch):
    """`--mode agent` routes through the token-free Agent client and writes docs."""
    manifest = tmp_path / "manifest.jsonl"
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 body")
    manifest.write_text(json.dumps({"doc_id": "docA", "pdf_path": str(pdf)}) + "\n")
    cfg = tmp_path / "mineru.yaml"
    cfg.write_text(
        "mode: agent\n"
        "agent:\n  base_url: http://test/agent\n  poll_interval_seconds: 0\n"
        f"outputs:\n  parsed_dir: {tmp_path}/parsed_docs\n"
    )

    def fake_post(url, headers=None, json=None, timeout=None):
        return _FakeResp(payload={"code": 0, "data": {"task_id": "T", "file_url": "http://oss/p"}})

    def fake_get(url, headers=None, timeout=None):
        if url.endswith("/parse/T"):
            return _FakeResp(
                payload={"code": 0, "data": {"state": "done", "markdown_url": "http://cdn/m.md"}}
            )
        return _FakeResp(text="# Paper\n\nKd = 50 nM.\n")

    monkeypatch.setattr(client_mod.requests, "post", fake_post)
    monkeypatch.setattr(client_mod.requests, "put", lambda *a, **k: _FakeResp(status_code=200))
    monkeypatch.setattr(client_mod.requests, "get", fake_get)

    rc = parse_main([
        "--manifest", str(manifest),
        "--config", str(cfg),
        "--run-dir", str(tmp_path / "runs" / "agent"),
    ])
    assert rc == 0
    md = (Path(tmp_path) / "parsed_docs" / "docA" / "document.md").read_text()
    assert "Kd = 50 nM" in md


def test_parse_cli_resume_skips(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps({"doc_id": "doc1", "pdf_path": "x.pdf"}) + "\n")
    cfg = tmp_path / "mineru.yaml"
    cfg.write_text(
        "mode: dry-run\n"
        f"outputs:\n  parsed_dir: {tmp_path}/parsed_docs\n"
    )
    run_dir = tmp_path / "runs" / "resumetest"

    assert parse_main(["--manifest", str(manifest), "--config", str(cfg),
                       "--run-dir", str(run_dir), "--dry-run"]) == 0
    assert parse_main(["--manifest", str(manifest), "--config", str(cfg),
                       "--run-dir", str(run_dir), "--dry-run", "--resume"]) == 0

    metrics = json.loads((run_dir / "metrics.json").read_text())
    assert metrics["skipped"] == 1
