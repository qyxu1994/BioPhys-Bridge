"""Run agent-task baselines against Biophys-Bridge cases.

The default ``lexical_baseline`` is deterministic and offline. API-backed
models are opt-in so the same harness can run in CI without secrets and later
resume paid benchmark runs from checkpoints.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from biophysevo.quality.validate_schema import validate_each
from biophysevo.utils.io import read_jsonl, safe_jsonl_writer
from biophysevo.utils.run_manager import (
    RunManager,
    add_common_run_flags,
    command_string,
    resolve_run_dir,
)


_WORD_RE = re.compile(r"[A-Za-z0-9_+\-.]+")


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _WORD_RE.findall(text or "") if len(t) > 2}


def _f1(predicted: set[str], gold: set[str]) -> float:
    if not predicted and not gold:
        return 1.0
    if not predicted or not gold:
        return 0.0
    overlap = len(predicted & gold)
    if overlap == 0:
        return 0.0
    precision = overlap / len(predicted)
    recall = overlap / len(gold)
    return 2 * precision * recall / (precision + recall)


def _evidence_map(case: dict[str, Any]) -> dict[str, str]:
    return {
        str(ev.get("evidence_id")): ev.get("text") or ""
        for ev in case.get("evidence", [])
    }


def _evidence_query(case: dict[str, Any], task: dict[str, Any]) -> str:
    model = case.get("biophysical_model") or {}
    interp = case.get("physical_interpretation") or {}
    mechanism = case.get("biological_mechanism") or {}
    qe_bits = []
    for qe in case.get("quantitative_evidence") or []:
        qe_bits.append(
            " ".join(
                str(qe.get(k) or "")
                for k in ("metric", "condition", "unit", "normalized_unit")
            )
        )
    return " ".join(
        [
            str(task.get("task_type") or ""),
            str(task.get("input") or ""),
            str(case.get("research_question") or ""),
            str(case.get("domain") or ""),
            str(model.get("model_name") or ""),
            str(model.get("model_family") or ""),
            str(model.get("equation_latex") or ""),
            str(interp.get("directionality") or ""),
            str(mechanism.get("description") or ""),
            " ".join(qe_bits),
        ]
    )


def select_evidence_candidates(
    case: dict[str, Any],
    task: dict[str, Any],
    *,
    max_blocks: int = 48,
) -> list[tuple[str, str]]:
    """Rank candidate evidence without reading task gold evidence IDs.

    The benchmark asks models to choose supporting evidence IDs, so the prompt
    must not be pre-filtered by ``task["supporting_evidence_ids"]``. This
    deterministic retriever only sees the task input and public case fields.
    """
    evidence = _evidence_map(case)
    query_tokens = _tokens(_evidence_query(case, task))
    quantitative_ids = {
        str(qe.get("evidence_id"))
        for qe in case.get("quantitative_evidence") or []
        if qe.get("evidence_id")
    }
    scored: list[tuple[float, str, str]] = []
    for eid, text in evidence.items():
        ev_tokens = _tokens(text)
        overlap = len(query_tokens & ev_tokens)
        score = overlap / max(len(query_tokens), 1)
        if eid in quantitative_ids:
            score += 0.15
        if any(tok in ev_tokens for tok in ("table", "fig", "figure", "equation")):
            score += 0.03
        scored.append((score, eid, text))
    scored.sort(key=lambda item: (-item[0], item[1]))
    selected = scored[:max_blocks] if max_blocks > 0 else scored
    return [(eid, text) for _, eid, text in selected]


def build_prompt(
    case: dict[str, Any],
    task: dict[str, Any],
    *,
    max_evidence_blocks: int = 48,
    evidence_chars: int = 900,
) -> str:
    """Build the canonical evidence-grounded agent prompt."""
    evidence_lines = [
        f"- {eid}: {text[:evidence_chars]}"
        for eid, text in select_evidence_candidates(
            case,
            task,
            max_blocks=max_evidence_blocks,
        )
    ]
    model = case.get("biophysical_model") or {}
    interp = case.get("physical_interpretation") or {}
    mechanism = case.get("biological_mechanism") or {}
    return "\n".join(
        [
            "You are answering a Biophys-Bridge physics-grounded biology task.",
            "Use only the evidence below. Return JSON with keys answer and supporting_evidence_ids.",
            "Choose supporting_evidence_ids from the candidate evidence IDs below; gold IDs are not provided.",
            f"Domain: {case.get('domain')}",
            f"Task type: {task.get('task_type')}",
            f"Physical model: {model.get('model_name')} ({model.get('model_family')})",
            f"Equation: {model.get('equation_latex')}",
            f"Physical directionality: {interp.get('directionality')}",
            f"Biological mechanism: {mechanism.get('description')}",
            "Evidence:",
            *evidence_lines,
            f"Question: {task.get('input')}",
        ]
    )


def _lexical_baseline(case: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    candidates = select_evidence_candidates(case, task, max_blocks=3)
    cited = [eid for eid, _ in candidates]
    snippets = [text for _, text in candidates]
    model = case.get("biophysical_model") or {}
    interp = case.get("physical_interpretation") or {}
    mechanism = case.get("biological_mechanism") or {}
    answer = (
        f"Using {model.get('model_name')} and the cited quantitative evidence, "
        f"the physical directionality is: {interp.get('directionality')} "
        f"This supports the mechanism: {mechanism.get('description')} "
        f"Most relevant evidence: {' '.join(snippets)[:1200]}"
    )
    return {"answer": answer, "supporting_evidence_ids": cited}


def _parse_model_json(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"answer": text, "supporting_evidence_ids": []}
    if not isinstance(parsed, dict):
        return {"answer": str(parsed), "supporting_evidence_ids": []}
    return {
        "answer": str(parsed.get("answer") or ""),
        "supporting_evidence_ids": list(parsed.get("supporting_evidence_ids") or []),
    }


def _call_openai_compatible(
    *,
    model: str,
    prompt: str,
    api_key_env: str,
    base_url: str | None = None,
) -> dict[str, Any]:
    api_key = os.getenv(api_key_env)
    if not api_key:
        raise RuntimeError(f"{api_key_env} is required for model {model!r}")
    from openai import OpenAI  # type: ignore

    client = OpenAI(api_key=api_key, base_url=base_url)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )
    return _parse_model_json(resp.choices[0].message.content or "")


def _call_anthropic(*, model: str, prompt: str) -> dict[str, Any]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is required for Anthropic models")
    import anthropic  # type: ignore

    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model,
        max_tokens=800,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(
        block.text for block in resp.content if getattr(block, "type", None) == "text"
    )
    return _parse_model_json(text)


def call_model(provider: str, model: str, prompt: str, case: dict, task: dict) -> dict:
    if provider == "lexical":
        return _lexical_baseline(case, task)
    if provider == "openai":
        return _call_openai_compatible(
            model=model,
            prompt=prompt,
            api_key_env="OPENAI_API_KEY",
        )
    if provider == "deepseek":
        return _call_openai_compatible(
            model=model,
            prompt=prompt,
            api_key_env="DEEPSEEK_API_KEY",
            base_url="https://api.deepseek.com",
        )
    if provider == "openrouter":
        return _call_openai_compatible(
            model=model,
            prompt=prompt,
            api_key_env="OPENROUTER_API_KEY",
            base_url="https://openrouter.ai/api/v1",
        )
    if provider == "anthropic":
        return _call_anthropic(model=model, prompt=prompt)
    raise ValueError(f"unknown provider: {provider}")


def score_prediction(task: dict[str, Any], prediction: dict[str, Any]) -> dict[str, float]:
    answer_f1 = _f1(_tokens(prediction.get("answer") or ""), _tokens(task.get("gold_answer") or ""))
    evidence_f1 = _f1(
        {str(x) for x in prediction.get("supporting_evidence_ids") or []},
        {str(x) for x in task.get("supporting_evidence_ids") or []},
    )
    return {
        "answer_token_f1": answer_f1,
        "evidence_id_f1": evidence_f1,
        "overall_score": 0.7 * answer_f1 + 0.3 * evidence_f1,
    }


def _infer_provider(model: str, provider: str | None) -> str:
    if provider:
        return provider
    if model == "lexical_baseline":
        return "lexical"
    if model.startswith("claude"):
        return "anthropic"
    if model.startswith("deepseek"):
        return "deepseek"
    if "/" in model:
        return "openrouter"
    return "openai"


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_domain: dict[str, list[float]] = defaultdict(list)
    by_task_type: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        score = float(row["scores"]["overall_score"])
        by_domain[row["domain"]].append(score)
        by_task_type[row["task_type"]].append(score)
    return {
        "n_tasks": len(rows),
        "mean_overall_score": (
            sum(float(r["scores"]["overall_score"]) for r in rows) / len(rows)
            if rows
            else 0.0
        ),
        "mean_answer_token_f1": (
            sum(float(r["scores"]["answer_token_f1"]) for r in rows) / len(rows)
            if rows
            else 0.0
        ),
        "mean_evidence_id_f1": (
            sum(float(r["scores"]["evidence_id_f1"]) for r in rows) / len(rows)
            if rows
            else 0.0
        ),
        "domain_scores": {
            key: sum(vals) / len(vals) for key, vals in sorted(by_domain.items())
        },
        "task_type_scores": {
            key: sum(vals) / len(vals) for key, vals in sorted(by_task_type.items())
        },
        "task_type_counts": dict(Counter(r["task_type"] for r in rows)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Biophys-Bridge agent-task eval.")
    parser.add_argument("--input", type=Path, default=Path("data/release/biophys_bridge_evo_cases.jsonl"))
    parser.add_argument("--model", default="lexical_baseline")
    parser.add_argument("--provider", choices=["lexical", "openai", "anthropic", "deepseek", "openrouter"])
    parser.add_argument(
        "--aggregate-out",
        type=Path,
        help="Optional immutable metrics JSON path; refuses to overwrite.",
    )
    add_common_run_flags(parser)
    args = parser.parse_args(argv)

    if args.aggregate_out and args.aggregate_out.exists():
        print(f"refusing to overwrite aggregate-out: {args.aggregate_out}", file=sys.stderr)
        return 2

    raw = list(read_jsonl(args.input))
    if args.limit is not None:
        raw = raw[: args.limit]
    valid, errors = validate_each(raw)
    if errors:
        print(f"refusing to evaluate: {len(errors)} schema errors", file=sys.stderr)
        return 1

    provider = _infer_provider(args.model, args.provider)
    run = RunManager(
        resolve_run_dir(args, f"agent_eval_{provider}_{args.model}"),
        config={"input": str(args.input), "model": args.model, "provider": provider},
        command=command_string(),
    )
    ckpt = run.checkpoint_store("agent_eval")
    out_path = run.run_dir / "predictions.jsonl"
    if out_path.exists() and not args.resume:
        ckpt.close()
        run.close()
        print(
            f"refusing to append duplicate predictions without --resume: {out_path}",
            file=sys.stderr,
        )
        return 2
    rows: list[dict[str, Any]] = []

    try:
        with safe_jsonl_writer(out_path) as writer:
            for case in valid:
                case_dict = json.loads(case.model_dump_json())
                for task_idx, task in enumerate(case_dict.get("agent_tasks") or []):
                    item_id = f"{case.case_id}::{task_idx}::{args.model}"
                    if args.resume and ckpt.is_done(item_id):
                        continue
                    prompt = build_prompt(case_dict, task)
                    prediction = call_model(provider, args.model, prompt, case_dict, task)
                    scores = score_prediction(task, prediction)
                    row = {
                        "id": item_id,
                        "case_id": case.case_id,
                        "domain": case.domain,
                        "task_type": task.get("task_type"),
                        "model": args.model,
                        "provider": provider,
                        "prediction": prediction,
                        "scores": scores,
                    }
                    writer.write(row)
                    run.manifest.write({"id": item_id, "case_id": case.case_id})
                    ckpt.mark_done(item_id)
                    rows.append(row)
    finally:
        ckpt.close()

    # Include previous rows when resuming so metrics describe the whole output file.
    all_rows = list(read_jsonl(out_path))
    metrics = {
        "model": args.model,
        "provider": provider,
        "schema_errors": len(errors),
        "evaluated_this_run": len(rows),
        **_aggregate(all_rows),
    }
    run.write_metrics(metrics)
    run.close()

    if args.aggregate_out:
        args.aggregate_out.parent.mkdir(parents=True, exist_ok=True)
        args.aggregate_out.write_text(json.dumps(metrics, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    sys.exit(main())
