import json

from biophysevo.extraction import enrich_cases as EC


def test_cli_enriches_and_attaches_consistency(tmp_path, monkeypatch):
    case = {
        "case_id": "biophysevo_000001",
        "evidence": [{"evidence_id": "e1", "modality": "table", "text": "Kd=14 nM"},
                     {"evidence_id": "e2", "modality": "text", "text": "dG=-8.46 kcal/mol"}],
        "quantitative_evidence": [
            {"metric": "Kd", "value": 14.0, "unit": "nM", "evidence_id": "e1"},
            {"metric": "binding free energy", "value": -8.46, "unit": "kcal/mol", "evidence_id": "e2"}],
    }
    inp = tmp_path / "in.jsonl"
    inp.write_text(json.dumps(case) + "\n")
    out = tmp_path / "out.jsonl"

    def fake_enrich(c, *, enabled, model="gpt-4o", client=None):
        c = dict(c)
        c["agent_tasks"] = [{"task_type": "derivation", "input": "i",
                             "gold_answer": "g", "supporting_evidence_ids": ["e1"]}]
        return c
    monkeypatch.setattr(EC.enrich_case_mod, "enrich_case", fake_enrich)

    rc = EC.main(["--input", str(inp), "--out", str(out), "--run-dir", str(tmp_path / "run")])
    assert rc == 0
    rec = json.loads(out.read_text().splitlines()[0])
    assert rec["agent_tasks"][0]["task_type"] == "derivation"

    cons = json.loads((tmp_path / "out.jsonl.consistency.jsonl").read_text().splitlines()[0])
    assert cons["case_id"] == "biophysevo_000001"
    # Kd=14nM vs dG=-8.46 -> residual ~2.25 > default 2.0 tol -> inconsistent (T-mismatch flagged)
    assert cons["physics_consistency"]["status"] == "inconsistent"
    assert cons["physics_consistency"]["relation"] == "dG = RT ln(K)"


def test_cli_records_enrich_failure_without_aborting(tmp_path, monkeypatch):
    rows = [
        {"case_id": "bad", "evidence": [], "quantitative_evidence": []},
        {"case_id": "good", "evidence": [], "quantitative_evidence": []},
    ]
    inp = tmp_path / "in.jsonl"
    inp.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    out = tmp_path / "out.jsonl"

    def fake_enrich(c, *, enabled, model="gpt-4o", client=None):
        if c["case_id"] == "bad":
            raise RuntimeError("temporary model error")
        return c

    monkeypatch.setattr(EC.enrich_case_mod, "enrich_case", fake_enrich)
    rc = EC.main(["--input", str(inp), "--out", str(out), "--run-dir", str(tmp_path / "run")])
    assert rc == 0
    assert len(out.read_text().splitlines()) == 1
    assert "temporary model error" in (tmp_path / "run" / "manifest.jsonl").read_text()


def test_cli_stops_on_quota_error_without_checkpointing_rest(tmp_path, monkeypatch):
    rows = [
        {"case_id": "done", "evidence": [], "quantitative_evidence": []},
        {"case_id": "quota", "evidence": [], "quantitative_evidence": []},
        {"case_id": "later", "evidence": [], "quantitative_evidence": []},
    ]
    inp = tmp_path / "in.jsonl"
    inp.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    out = tmp_path / "out.jsonl"

    def fake_enrich(c, *, enabled, model="gpt-4o", client=None):
        if c["case_id"] == "quota":
            raise RuntimeError("Error code: 429 - insufficient_quota")
        return c

    monkeypatch.setattr(EC.enrich_case_mod, "enrich_case", fake_enrich)
    rc = EC.main(["--input", str(inp), "--out", str(out), "--run-dir", str(tmp_path / "run")])
    assert rc == 2
    assert len(out.read_text().splitlines()) == 1
    manifest = (tmp_path / "run" / "manifest.jsonl").read_text()
    assert "blocked_quota" in manifest
    ckpt = (tmp_path / "run" / "checkpoints" / "enrich.jsonl").read_text()
    assert "done" in ckpt
    assert "quota" not in ckpt
    assert "later" not in ckpt
