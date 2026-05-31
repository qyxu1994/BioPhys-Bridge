"""Evidence-only LLM enrichment of an existing case (opt-in, gpt-4o).

Adds a real multi-step trajectory, a populated biophysical_model, grounded
failure_or_revision (only if cited), and a diverse agent_tasks list. Audited
quantitative_evidence is preserved verbatim. Anti-fabrication: every cited
evidence_id must exist in the case's evidence[]; fabricated ids are dropped.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any

from biophysevo.schemas.case_schema import (
    DOMAIN_DEFAULT_MODEL_FAMILY,
    DOMAIN_MODEL_FAMILY_COMPATIBILITY,
    MODEL_FAMILY_VALUES,
)

from .llm_fill import trim_evidence_blocks

SYSTEM_PROMPT = (
    "You enrich a structured scientific case with its reasoning trajectory. You are "
    "given the case's evidence blocks (each with an evidence_id) and its already-"
    "verified quantitative_evidence (DO NOT change these values). Produce ONE JSON "
    "object with keys:\n"
    "- sci_evo_trajectory: array of steps {step_id, stage, description, "
    "input_evidence_ids, reasoning, output}. stage in [research_question, hypothesis, "
    "method_design, quantitative_observation, biophysical_interpretation, "
    "failure_or_revision, next_step]. Give real reasoning per step.\n"
    "- biophysical_model: {model_name, model_family, secondary_model_families, "
    "equation_latex, variables (obj), assumptions (array), validity_conditions "
    "(array)} reflecting the actual governing physics. model_family must be one "
    "of [binding_thermodynamics, enzyme_reaction_kinetics, "
    "folding_stability_thermodynamics, conformational_allostery_energy_landscape, "
    "polymer_phase_separation_statistical_mechanics, systems_stochastic_dynamics, "
    "mechanical_force_response, spatial_transport_electrostatics, "
    "evolutionary_fitness_landscape].\n"
    "- physical_interpretation: {derived_quantity, directionality, consistency_check, "
    "caveats (array)}. Explain quantitative directionality and whether the reported "
    "numbers are internally consistent with the model.\n"
    "- biological_mechanism: {mechanism_type, description, structure_function_link, "
    "mutation_or_ligand_effect}. Tie the physical model to biological mechanism.\n"
    "- failure_or_revision: {present (bool), description, revision_decision, evidence_ids} "
    "ONLY if the paper actually reports a failure/revision; else present=false.\n"
    "- agent_tasks: array of 3-4 tasks {task_type, input, gold_answer, "
    "supporting_evidence_ids, required_reasoning_skills, allowed_tools}. Use task_types: "
    "derivation, discrepancy_explanation, mechanism_from_evidence, next_experiment_design.\n"
    "RULES: use ONLY the provided evidence; never invent values or evidence_ids; every "
    "input_evidence_ids / supporting_evidence_ids / failure evidence_ids MUST be ids that "
    "appear in the input. If unsupported, use null or an empty array."
)


def build_messages(case: dict) -> list[dict]:
    payload = {
        "evidence_blocks": trim_evidence_blocks(case.get("evidence", [])),
        "quantitative_evidence": case.get("quantitative_evidence", []),
        "research_question": case.get("research_question"),
        "domain": case.get("domain"),
    }
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def _filter_ids(ids: Any, valid: set[str]) -> list[str]:
    return [i for i in (ids or []) if i in valid]


def _coerce_str(v: Any) -> str | None:
    """Schema requires str for free-text fields. LLM sometimes returns dict/list."""
    if v is None or isinstance(v, str):
        return v
    try:
        return json.dumps(v, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(v)


_DEFAULT_REASONING_SKILLS = [
    "evidence grounding",
    "quantitative model interpretation",
    "mechanism reasoning",
    "next-step design",
]
_DEFAULT_ALLOWED_TOOLS = [
    "MinerU parsed paper",
    "calculator",
    "domain literature",
]


def _coerce_vocab_list(value: Any, default: list[str]) -> list[str]:
    """Normalize LLM vocabulary fields without preserving character-split strings."""
    if isinstance(value, str):
        separators = [",", ";", "\n"]
        parts = [value]
        for sep in separators:
            if sep in value:
                parts = value.replace("\n", ",").replace(";", ",").split(",")
                break
    elif isinstance(value, list):
        parts = value
    else:
        parts = []

    cleaned: list[str] = []
    for part in parts:
        text = _coerce_str(part)
        if not text:
            continue
        text = " ".join(text.strip().split())
        if len(text) <= 1 or len(text) > 100:
            continue
        if text not in cleaned:
            cleaned.append(text)

    if len(cleaned) >= 8 and sum(len(item) <= 1 for item in cleaned) / len(cleaned) >= 0.8:
        return list(default)
    return cleaned or list(default)


def _coerce_variables(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, str] = {}
    for key, item in value.items():
        name = _coerce_str(key)
        description = _coerce_str(item)
        if name and description:
            out[name] = description
    return out


def _primary_evidence_id(case: dict) -> str | None:
    for qe in case.get("quantitative_evidence", []):
        eid = qe.get("evidence_id")
        if eid:
            return eid
    for evidence in case.get("evidence", []):
        eid = evidence.get("evidence_id")
        if eid:
            return eid
    return None


def _ensure_next_step(case: dict, trajectory: list[dict]) -> list[dict]:
    if any(step.get("stage") == "next_step" for step in trajectory):
        return trajectory
    eid = _primary_evidence_id(case)
    next_task = next(
        (
            task for task in case.get("agent_tasks", [])
            if task.get("task_type") == "next_experiment_design"
        ),
        None,
    )
    trajectory.append({
        "step_id": "step_next",
        "stage": "next_step",
        "description": "Prioritize the next experiment or computation that tests the physics-to-mechanism interpretation.",
        "input_evidence_ids": [eid] if eid else [],
        "reasoning": "The next step should probe the mechanism implied by the quantitative model while preserving evidence grounding.",
        "output": (
            next_task.get("gold_answer")
            if next_task and next_task.get("gold_answer")
            else "Design a focused follow-up that perturbs the modeled physical quantity and checks whether the predicted biological response changes accordingly."
        ),
    })
    return trajectory


def _apply(case: dict, fields: dict) -> dict:
    valid = {e.get("evidence_id") for e in case.get("evidence", []) if e.get("evidence_id")}
    out = dict(case)  # preserves quantitative_evidence and evidence untouched
    out.pop("agent_task", None)  # drop legacy singular field (schema forbids extras)

    traj = []
    for i, s in enumerate(fields.get("sci_evo_trajectory") or [], start=1):
        s = dict(s)
        sid = s.get("step_id")
        traj.append({
            "step_id": str(sid) if sid not in (None, "") else f"step_{i:03d}",
            "stage": s.get("stage") or "biophysical_interpretation",
            "description": _coerce_str(s.get("description")) or "",
            "input_evidence_ids": _filter_ids(s.get("input_evidence_ids"), valid),
            "reasoning": _coerce_str(s.get("reasoning")),
            "output": _coerce_str(s.get("output")),
        })
    bm = fields.get("biophysical_model")
    if isinstance(bm, dict) and bm.get("model_name") and bm.get("equation_latex"):
        model_family = bm.get("model_family")
        compatible = DOMAIN_MODEL_FAMILY_COMPATIBILITY.get(out.get("domain"), set())
        previous_family = case.get("biophysical_model", {}).get("model_family")
        if model_family not in MODEL_FAMILY_VALUES or model_family not in compatible:
            model_family = (
                previous_family
                if previous_family in compatible
                else DOMAIN_DEFAULT_MODEL_FAMILY.get(out.get("domain"))
            )
        secondary = []
        for family in bm.get("secondary_model_families") or []:
            if (
                family in MODEL_FAMILY_VALUES
                and family != model_family
                and family not in secondary
            ):
                secondary.append(family)
        out["biophysical_model"] = {
            "model_name": _coerce_str(bm.get("model_name")) or "",
            "model_family": model_family,
            "secondary_model_families": secondary,
            "equation_latex": _coerce_str(bm.get("equation_latex")) or "",
            "variables": _coerce_variables(bm.get("variables")),
            "assumptions": [a for a in (bm.get("assumptions") or []) if isinstance(a, str)],
            "validity_conditions": [v for v in (bm.get("validity_conditions") or []) if isinstance(v, str)],
        }

    fr = fields.get("failure_or_revision")
    if isinstance(fr, dict) and fr.get("present"):
        eids = _filter_ids(fr.get("evidence_ids"), valid)
        out["failure_or_revision"] = (
            {
                "present": True,
                "description": fr.get("description"),
                "revision_decision": fr.get("revision_decision"),
                "evidence_ids": eids,
                "inferred_from_discussion": False,
            }
            if eids
            else None
        )
    else:
        out["failure_or_revision"] = None

    tasks = []
    for t in fields.get("agent_tasks") or []:
        sup = _filter_ids(t.get("supporting_evidence_ids"), valid)
        if not sup:
            continue  # a task must cite real evidence (schema invariant)
        tasks.append({
            "task_type": t.get("task_type") or "next_experiment_design",
            "input": _coerce_str(t.get("input")) or "",
            "gold_answer": _coerce_str(t.get("gold_answer")) or "",
            "supporting_evidence_ids": sup,
            "required_reasoning_skills": _coerce_vocab_list(
                t.get("required_reasoning_skills"),
                _DEFAULT_REASONING_SKILLS,
            ),
            "allowed_tools": _coerce_vocab_list(
                t.get("allowed_tools"),
                _DEFAULT_ALLOWED_TOOLS,
            ),
        })
    if tasks:
        out["agent_tasks"] = tasks

    if traj:
        out["sci_evo_trajectory"] = _ensure_next_step(out, traj)

    pi = fields.get("physical_interpretation")
    if isinstance(pi, dict) and pi.get("directionality") and pi.get("consistency_check"):
        out["physical_interpretation"] = {
            "derived_quantity": _coerce_str(pi.get("derived_quantity")),
            "directionality": _coerce_str(pi.get("directionality")) or "",
            "consistency_check": _coerce_str(pi.get("consistency_check")) or "",
            "caveats": [
                _coerce_str(c) or ""
                for c in (pi.get("caveats") or [])
                if _coerce_str(c)
            ],
        }

    bmec = fields.get("biological_mechanism")
    if isinstance(bmec, dict) and bmec.get("mechanism_type") and bmec.get("description"):
        out["biological_mechanism"] = {
            "mechanism_type": _coerce_str(bmec.get("mechanism_type")) or "",
            "description": _coerce_str(bmec.get("description")) or "",
            "structure_function_link": _coerce_str(bmec.get("structure_function_link")),
            "mutation_or_ligand_effect": _coerce_str(bmec.get("mutation_or_ligand_effect")),
        }
    return out


def enrich_case(case: dict, *, enabled: bool = False, model: str = "gpt-4o", client: Any = None) -> dict:
    if not enabled:
        return case
    if client is None:
        if not os.environ.get("OPENAI_API_KEY"):
            return case
        try:
            from openai import OpenAI
        except ImportError:
            return case
        client = OpenAI()
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=build_messages(case),
                response_format={"type": "json_object"},
            )
            break
        except Exception as exc:  # noqa: BLE001 - transient API/network errors are common in batches.
            last_exc = exc
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    else:  # pragma: no cover - loop always breaks or raises.
        raise last_exc or RuntimeError("LLM enrichment failed")
    content = resp.choices[0].message.content or "{}"
    try:
        fields = json.loads(content)
    except json.JSONDecodeError:
        return case
    return _apply(case, fields)
