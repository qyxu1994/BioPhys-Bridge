"""Agent-task baseline evaluation harness."""

from __future__ import annotations

import json

from biophysevo.evaluation.run_agent_eval import (
    _lexical_baseline,
    build_prompt,
    main as agent_eval_main,
)


def test_agent_eval_lexical_baseline(tmp_path, sample_case_dict):
    inp = tmp_path / "cases.jsonl"
    inp.write_text(json.dumps(sample_case_dict) + "\n")
    aggregate = tmp_path / "aggregate.json"
    rc = agent_eval_main([
        "--input", str(inp),
        "--model", "lexical_baseline",
        "--run-dir", str(tmp_path / "run"),
        "--aggregate-out", str(aggregate),
    ])
    assert rc == 0
    metrics = json.loads(aggregate.read_text())
    assert metrics["model"] == "lexical_baseline"
    assert metrics["provider"] == "lexical"
    assert metrics["n_tasks"] == 1
    assert 0.0 <= metrics["mean_overall_score"] <= 1.0
    assert (tmp_path / "run" / "predictions.jsonl").exists()


def test_agent_eval_refuses_to_overwrite_aggregate(tmp_path, sample_case_dict):
    inp = tmp_path / "cases.jsonl"
    inp.write_text(json.dumps(sample_case_dict) + "\n")
    aggregate = tmp_path / "aggregate.json"
    aggregate.write_text("{}")
    rc = agent_eval_main([
        "--input", str(inp),
        "--model", "lexical_baseline",
        "--run-dir", str(tmp_path / "run"),
        "--aggregate-out", str(aggregate),
    ])
    assert rc == 2


def test_prompt_does_not_filter_to_gold_support_ids(sample_case_dict):
    case = json.loads(json.dumps(sample_case_dict))
    case["evidence"] = [
        {
            "evidence_id": "ev_decoy",
            "modality": "text",
            "text": "allosteric enzyme kinetics rate law and mechanism evidence",
            "source_location": {},
            "mineru_artifact_path": None,
        },
        {
            "evidence_id": "ev_gold",
            "modality": "text",
            "text": "unrelated prose with no query terms",
            "source_location": {},
            "mineru_artifact_path": None,
        },
    ]
    task = {
        "task_type": "mechanism_from_evidence",
        "input": "Explain the allosteric enzyme kinetics mechanism.",
        "gold_answer": "gold",
        "supporting_evidence_ids": ["ev_gold"],
    }

    prompt = build_prompt(case, task, max_evidence_blocks=1)

    assert "ev_decoy" in prompt
    assert "ev_gold" not in prompt


def test_lexical_baseline_does_not_copy_gold_support_ids(sample_case_dict):
    case = json.loads(json.dumps(sample_case_dict))
    case["evidence"] = [
        {
            "evidence_id": "ev_decoy",
            "modality": "text",
            "text": "binding thermodynamics and quantitative mechanism evidence",
            "source_location": {},
            "mineru_artifact_path": None,
        },
        {
            "evidence_id": "ev_gold",
            "modality": "text",
            "text": "unrelated prose",
            "source_location": {},
            "mineru_artifact_path": None,
        },
    ]
    task = {
        "task_type": "mechanism_from_evidence",
        "input": "Use binding thermodynamics to explain mechanism.",
        "gold_answer": "gold",
        "supporting_evidence_ids": ["ev_gold"],
    }

    pred = _lexical_baseline(case, task)

    assert pred["supporting_evidence_ids"] != ["ev_gold"]
    assert pred["supporting_evidence_ids"][0] == "ev_decoy"
