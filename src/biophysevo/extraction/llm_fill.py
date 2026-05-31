"""Evidence-only LLM extraction (opt-in). Fills quantitative_evidence + the
stub fields the regex builder cannot derive, grounded to evidence_id.

Anti-fabrication: any evidence_id not present in the doc's real blocks is
dropped before the fields are used (the project's "never invent data" invariant).
Disabled by default; returns ``None`` when the LLM is off or unavailable so the
caller falls back to templates.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

from biophysevo.schemas.case_schema import MODEL_FAMILY_VALUES

MAX_BLOCK_CHARS = 1200
MAX_PROMPT_CHARS = 90000

SYSTEM_PROMPT = (
    "You extract structured scientific evidence from one paper's parsed evidence "
    "blocks (tables, formulas, figure captions, and numbered prose paragraphs, "
    "each with an evidence_id). Return ONE JSON object with EXACTLY these keys:\n"
    "- domain: one of [protein_ligand_binding, enzyme_kinetics, "
    "protein_stability_thermodynamics, conformational_dynamics_allostery, "
    "biomolecular_phase_separation, systems_biology_dynamics]\n"
    "- quantitative_evidence: array of objects "
    "{metric, value (a number), unit, condition, evidence_id}\n"
    "- model_family: one of [binding_thermodynamics, enzyme_reaction_kinetics, "
    "folding_stability_thermodynamics, conformational_allostery_energy_landscape, "
    "polymer_phase_separation_statistical_mechanics, systems_stochastic_dynamics, "
    "mechanical_force_response, spatial_transport_electrostatics, "
    "evolutionary_fitness_landscape]\n"
    "- secondary_model_families: array using the same vocabulary; include only "
    "supporting model families, not the primary one\n"
    "- physical_interpretation: {derived_quantity, directionality, "
    "consistency_check, caveats (array of strings)}\n"
    "- biological_mechanism: {mechanism_type, description, "
    "structure_function_link, mutation_or_ligand_effect}\n"
    "- research_question: string\n"
    "- gold_answer: string\n"
    "- supporting_evidence_ids: array of evidence_id\n"
    "RULES: Use ONLY the provided evidence blocks. Never invent values. Every "
    "value and every claim MUST cite an evidence_id that appears in the input. "
    "Extract the 3-8 most important quantitative results. Prefer physical "
    "quantities that carry a real unit (e.g. Kd, Km, kcat, Tm, dG/ddG, Csat, "
    "rate constants). For each: 'value' MUST be a single number (no ranges, no "
    "text); 'unit' MUST be a standard unit symbol (e.g. nM, uM, kcal/mol, "
    "kJ/mol, s^-1, degC) or \"dimensionless\"; put any range, qualifier, "
    "organism, or assay condition in 'condition'. If a paragraph only gives a "
    "range, use one representative endpoint as the value and state the range in "
    "'condition'. If the evidence does not support a field, use null or an "
    "empty array."
)


def _block_priority(block: dict) -> tuple[int, int]:
    text = str(block.get("text") or "")
    lowered = text.lower()
    metric_hit = any(
        token in text
        for token in ("Kd", "Ki", "IC50", "EC50", "Km", "kcat", "Tm", "ΔG", "ΔΔG")
    )
    model_hit = any(
        token in lowered
        for token in (
            "equation",
            "thermodynamic",
            "kinetic",
            "binding",
            "phase separation",
            "alloster",
            "fitness",
            "diffusion",
        )
    )
    numeric = any(ch.isdigit() for ch in text)
    modality_bonus = 2 if block.get("modality") in {"table", "formula"} else 0
    return (int(metric_hit) * 5 + int(model_hit) * 3 + int(numeric) + modality_bonus, -len(text))


def trim_evidence_blocks(
    evidence_blocks: list[dict],
    *,
    max_total_chars: int = MAX_PROMPT_CHARS,
    max_block_chars: int = MAX_BLOCK_CHARS,
) -> list[dict]:
    """Keep the most quantitative/model-bearing evidence blocks under budget."""

    selected = []
    used = 0
    for block in sorted(evidence_blocks, key=_block_priority, reverse=True):
        text = str(block.get("text") or "")
        trimmed = text[:max_block_chars]
        cost = len(trimmed)
        if selected and used + cost > max_total_chars:
            continue
        out = {
            "evidence_id": block.get("evidence_id"),
            "modality": block.get("modality"),
            "source_location": block.get("source_location"),
            "text": trimmed,
        }
        selected.append(out)
        used += cost
        if used >= max_total_chars:
            break
    return selected


def build_messages(evidence_blocks: list[dict]) -> list[dict]:
    user = json.dumps(
        {"evidence_blocks": trim_evidence_blocks(evidence_blocks)},
        ensure_ascii=False,
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_against_evidence(fields: dict, valid_ids: set[str]) -> dict:
    """Drop any quantitative_evidence row or supporting id citing an evidence_id
    not in ``valid_ids``, or whose value is non-numeric."""
    out = dict(fields)
    out["quantitative_evidence"] = [
        row
        for row in (fields.get("quantitative_evidence") or [])
        if row.get("evidence_id") in valid_ids and _is_number(row.get("value"))
    ]
    out["supporting_evidence_ids"] = [
        i for i in (fields.get("supporting_evidence_ids") or []) if i in valid_ids
    ]
    if fields.get("model_family") not in MODEL_FAMILY_VALUES:
        out.pop("model_family", None)
    secondary = []
    for family in fields.get("secondary_model_families") or []:
        if (
            family in MODEL_FAMILY_VALUES
            and family != out.get("model_family")
            and family not in secondary
        ):
            secondary.append(family)
    out["secondary_model_families"] = secondary
    return out


def extract_case_fields(
    evidence_blocks: list[dict],
    *,
    enabled: bool = False,
    model: str = "gpt-4o",
    client: Any = None,
) -> dict | None:
    """Call the LLM and return validated fields, or ``None`` if disabled/unavailable."""
    if not enabled:
        return None
    valid_ids = {b.get("evidence_id") for b in evidence_blocks if b.get("evidence_id")}
    if client is None:
        if not os.environ.get("OPENAI_API_KEY"):
            return None
        try:
            from openai import OpenAI
        except ImportError:
            return None
        client = OpenAI()
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=build_messages(evidence_blocks),
                response_format={"type": "json_object"},
            )
            break
        except Exception as exc:  # noqa: BLE001 - transient API/network errors are resumable.
            last_exc = exc
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    else:  # pragma: no cover - loop always breaks or raises.
        raise last_exc or RuntimeError("LLM extraction failed")
    content = resp.choices[0].message.content or "{}"
    try:
        fields = json.loads(content)
    except json.JSONDecodeError:
        return None
    return validate_against_evidence(fields, valid_ids)
