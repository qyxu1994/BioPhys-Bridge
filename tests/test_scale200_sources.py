"""Scale-to-200 source scoring and manual parse handoff utilities."""

from __future__ import annotations

import json
from pathlib import Path

from biophysevo.sources.scale200 import (
    audit_parsed_outputs,
    candidate_from_europepmc_result,
    download_batch_pdfs,
    is_release_compatible_license,
    pdf_candidate_urls,
    render_manual_parse_instructions,
    requests,
    score_candidate,
    select_parse_batch,
)


def test_score_candidate_assigns_domain_and_model_family():
    rec = {
        "paper_title": "Allosteric enzyme kinetics with kcat and Km measurements",
        "abstract": "Michaelis-Menten analysis reports kcat, Km, and feedback.",
        "doi": "10.1/example",
        "license": "CC-BY",
        "is_open_access": True,
    }
    scored = score_candidate(rec)
    assert scored["domain_guess"] == "enzyme_kinetics"
    assert scored["model_family_guess"] == "enzyme_reaction_kinetics"
    assert scored["triage_score"] > 0


def test_europepmc_result_normalizes_pdf_url_and_oa_flag():
    rec = candidate_from_europepmc_result(
        {
            "id": "123",
            "title": "Protein folding stability",
            "doi": "10.1/example",
            "isOpenAccess": "Y",
            "fullTextUrlList": {
                "fullTextUrl": [
                    {"url": "https://example.org/html", "documentStyle": "html"},
                    {"url": "https://example.org/paper.pdf", "documentStyle": "pdf"},
                ]
            },
        },
        query="protein folding",
    )
    assert rec["candidate_id"] == "123"
    assert rec["source_url"] == "https://example.org/paper.pdf"
    assert rec["is_open_access"] is True


def test_license_filter_allows_release_compatible_cc_only():
    assert is_release_compatible_license("CC-BY-4.0")
    assert is_release_compatible_license("CC0-1.0")
    assert not is_release_compatible_license("cc by-nc-sa")
    assert not is_release_compatible_license("unknown")


def test_select_parse_batch_is_deterministic_and_balances_families():
    candidates = [
        {
            "paper_title": f"paper {i}",
            "doi": f"10.1/{i}",
            "license": "CC-BY",
            "abstract": abstract,
        }
        for i, abstract in enumerate(
            [
                "kcat Km Michaelis-Menten",
                "phase separation LLPS critical concentration",
                "binding affinity Kd ITC",
                "bistability ODE feedback",
            ],
            start=1,
        )
    ]
    batch1 = select_parse_batch(candidates, batch_size=3)
    batch2 = select_parse_batch(candidates, batch_size=3)
    assert [r["doi"] for r in batch1] == [r["doi"] for r in batch2]
    assert len({r["model_family_guess"] for r in batch1}) == 3


def test_pdf_candidate_urls_adds_pmc_fallbacks():
    urls = pdf_candidate_urls(
        {"source_url": "https://example.org/a.pdf", "pmcid": "PMC123"}
    )
    assert urls[0] == "https://example.org/a.pdf"
    assert "https://pmc.ncbi.nlm.nih.gov/articles/PMC123/pdf/" in urls


class _Resp:
    def __init__(self, *, status_code=200, content=b"%PDF-1.4\nbody"):
        self.status_code = status_code
        self.content = content

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"status {self.status_code}")

    def iter_content(self, chunk_size=1):
        yield self.content


def test_download_batch_pdfs_writes_new_manifest_without_overwrite(monkeypatch, tmp_path):
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return _Resp()

    monkeypatch.setattr(requests, "get", fake_get)
    summary = download_batch_pdfs(
        [
            {
                "doc_id": "batch_001_0001",
                "source_url": "https://example.org/paper.pdf",
                "license": "CC-BY",
                "paper_title": "T",
            }
        ],
        out_dir=tmp_path / "batch",
    )
    assert summary["n_downloaded"] == 1
    local = (tmp_path / "batch" / "local_manifest.jsonl").read_text()
    assert "batch_001_0001.pdf" in local
    assert calls == ["https://example.org/paper.pdf"]


def test_download_batch_pdfs_refuses_nonempty_out_dir(tmp_path):
    out = tmp_path / "existing"
    out.mkdir()
    (out / "keep.txt").write_text("do not overwrite")
    try:
        download_batch_pdfs([], out_dir=out)
    except FileExistsError as exc:
        assert "refusing" in str(exc)
    else:
        raise AssertionError("expected FileExistsError")


def test_download_batch_pdfs_resume_reuses_existing_pdf(tmp_path):
    out = tmp_path / "existing"
    pdf_dir = out / "pdfs"
    pdf_dir.mkdir(parents=True)
    (pdf_dir / "DOC1.pdf").write_bytes(b"%PDF-1.4\nbody")
    summary = download_batch_pdfs(
        [{"doc_id": "DOC1", "source_url": "https://example.org/paper.pdf"}],
        out_dir=out,
        resume=True,
    )
    assert summary["n_already_downloaded"] == 1
    assert "DOC1.pdf" in (out / "local_manifest.jsonl").read_text()


def test_manual_parse_instructions_include_resume_command(tmp_path):
    text = render_manual_parse_instructions(
        manifest_path=Path("data/raw/parse_batches/batch_001_manifest.jsonl"),
        parsed_dir=Path("data/intermediate/parsed_docs_real"),
        run_dir=Path("runs/parse_batch_001"),
    )
    assert "python -m biophysevo.mineru.parse" in text
    assert "--resume" in text
    assert "audit-parse" in text


def test_audit_parsed_outputs_detects_missing_docs(tmp_path):
    parsed = tmp_path / "parsed"
    doc = parsed / "DOC1"
    doc.mkdir(parents=True)
    for name in ["document.md", "document.json", "evidence_blocks.jsonl", "parse_metadata.json"]:
        (doc / name).write_text("{}\n")
    report = audit_parsed_outputs(
        [{"doc_id": "DOC1"}, {"doc_id": "DOC2"}],
        parsed,
    )
    assert report["n_parsed"] == 1
    assert report["n_missing_or_incomplete"] == 1
    assert report["records"][1]["missing"]
