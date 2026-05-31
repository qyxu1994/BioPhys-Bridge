"""Release export and manual review queue."""

from __future__ import annotations

import json
from pathlib import Path

from biophysevo.export_release import main as release_main
from biophysevo.extraction.manual_review import main as review_main


def _release_ready_case(case: dict) -> dict:
    """Add the semantic fields required by the release content gate."""
    case = json.loads(json.dumps(case))
    case["sci_evo_trajectory"].append({
        "step_id": "step_next",
        "stage": "next_step",
        "description": "Design a structural follow-up experiment grounded in the measured binding evidence.",
        "input_evidence_ids": ["ev_001"],
        "reasoning": "The next experiment should use the quantitative binding result to localize the mechanism.",
        "output": "Prioritize co-crystallization or HDX-MS for binding-site confirmation.",
    })
    return case


def test_release_export(tmp_path, sample_case_dict):
    inp = tmp_path / "cases.jsonl"
    inp.write_text(json.dumps(_release_ready_case(sample_case_dict)) + "\n")
    out_dir = tmp_path / "release"
    rc = release_main([
        "--input", str(inp),
        "--out-dir", str(out_dir),
        "--min-quality-score", "0.5",
    ])
    assert rc == 0
    assert (out_dir / "biophys_bridge_evo_cases.jsonl").exists()
    assert (out_dir / "biophys_bridge_10_gold_samples.jsonl").exists()
    assert (out_dir / "biophys_bridge_30_gold_samples.jsonl").exists()
    assert (out_dir / "biophys_bridge_metadata.json").exists()
    assert (out_dir / "biophys_bridge_schema.json").exists()
    assert (out_dir / "data_card.md").exists()


def test_release_emits_three_block_view(tmp_path, sample_case_dict):
    inp = tmp_path / "cases.jsonl"
    inp.write_text(json.dumps(_release_ready_case(sample_case_dict)) + "\n")
    out_dir = tmp_path / "release"
    rc = release_main([
        "--input", str(inp), "--out-dir", str(out_dir), "--min-quality-score", "0.0",
    ])
    assert rc == 0
    view = out_dir / "biophys_bridge_sci_evo_view.jsonl"
    assert view.exists()
    rec = json.loads(view.read_text().splitlines()[0])
    assert {"initial_requirement", "design_compute_experiment_trajectory", "success_criteria"} <= set(rec)
    meta = json.loads((out_dir / "biophys_bridge_metadata.json").read_text())
    assert "physics_consistency_checked_rate" in meta
    assert meta["release_n"] == 1
    assert meta["source_n_valid"] == 1
    assert meta["physics_model_family_counts"] == {"binding_thermodynamics": 1}
    assert meta["equation_bearing_coverage"] == 1.0
    assert meta["physics_consistency_audit_coverage"] == 1.0
    assert meta["split_counts"] == {"test": 0, "train": 1, "validation": 0}
    assert "mean_modalities_per_case" in meta
    assert meta["excluded_below_score"] == 0
    assert meta["exclusion_counts_reconciled"] is True
    assert meta["built_n"] - meta["shipped_n"] == (
        meta["excluded_not_reviewed"]
        + meta["excluded_content_quality"]
        + meta["excluded_below_score"]
    )
    release_rec = json.loads((out_dir / "biophys_bridge_evo_cases.jsonl").read_text())
    assert "Deterministic physics audit:" in release_rec["physical_interpretation"]["consistency_check"]
    assert (out_dir / "splits" / "train.jsonl").exists()
    assert (out_dir / "splits" / "validation.jsonl").exists()
    assert (out_dir / "splits" / "test.jsonl").exists()


def test_release_filters_low_quality(tmp_path, sample_case_dict):
    inp = tmp_path / "cases.jsonl"
    inp.write_text(json.dumps(_release_ready_case(sample_case_dict)) + "\n")
    out_dir = tmp_path / "release2"
    rc = release_main([
        "--input", str(inp),
        "--out-dir", str(out_dir),
        "--min-quality-score", "1.5",  # impossibly high
    ])
    assert rc == 1


def test_release_excludes_unreviewed_cases(tmp_path, make_case):
    """A high-scoring case that is still ``needs_fix`` must not reach a release.

    Regex-built template cases score well on structural signals but are not
    grounded science; the documented invariant is they cannot ship unreviewed.
    """
    case = make_case()
    case["quality"]["manual_review_status"] = "needs_fix"
    inp = tmp_path / "cases.jsonl"
    inp.write_text(json.dumps(case) + "\n")
    out_dir = tmp_path / "release3"
    rc = release_main([
        "--input", str(inp),
        "--out-dir", str(out_dir),
        "--min-quality-score", "0.0",  # score gate wide open
    ])
    assert rc == 1  # nothing reviewed -> empty release refused


def test_release_excludes_content_quality_failures(tmp_path, make_case):
    case = _release_ready_case(make_case())
    case["physical_interpretation"]["directionality"] = (
        "[template - needs expert review] directionality pending"
    )
    inp = tmp_path / "cases.jsonl"
    inp.write_text(json.dumps(case) + "\n")
    out_dir = tmp_path / "release_content_gate"
    rc = release_main([
        "--input", str(inp),
        "--out-dir", str(out_dir),
        "--min-quality-score", "0.0",
    ])
    assert rc == 1


def test_release_excludes_malformed_task_vocabularies(tmp_path, make_case):
    case = _release_ready_case(make_case())
    task = case["agent_tasks"][0]
    task["input"] = "[\"ev_001\"]"
    task["required_reasoning_skills"] = list("bad vocabulary")
    inp = tmp_path / "cases.jsonl"
    inp.write_text(json.dumps(case) + "\n")
    out_dir = tmp_path / "release_bad_vocab"
    rc = release_main([
        "--input", str(inp),
        "--out-dir", str(out_dir),
        "--min-quality-score", "0.0",
    ])
    assert rc == 1


def test_manual_review_queue(tmp_path, sample_case_dict):
    inp = tmp_path / "cases.jsonl"
    inp.write_text(json.dumps(sample_case_dict) + "\n")
    out = tmp_path / "queue.jsonl"
    rc = review_main(["--input", str(inp), "--out", str(out)])
    assert rc == 0
    queue = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    assert queue and queue[0]["review_status"] == "unreviewed"
