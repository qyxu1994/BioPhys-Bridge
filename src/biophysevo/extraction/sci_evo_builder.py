"""Biophys-Bridge / Sci-Evo case builder: candidates -> schema-valid Case dicts.

Evidence-only contract: every quantitative claim and every gold_answer must
reference at least one evidence_id from the doc's evidence_blocks. If evidence
is missing, the field is left null (never invented).

Schema-required fields that the regex pipeline cannot derive from evidence
(physical_interpretation, biological_mechanism, and parts of biophysical_model)
are written as explicitly-templated stubs containing the marker
``[template - needs expert review]`` so they are never mistaken for grounded
science. Cases produced here are marked ``manual_review_status="needs_fix"``
with a low quality score so they are gated out of release until an LLM or
human reviewer fills the templates with evidence-grounded content.
"""

from __future__ import annotations

from typing import Any, Iterable

from biophysevo.schemas.case_schema import (
    DOMAIN_BRIDGE_COMPATIBILITY,
    DOMAIN_DEFAULT_MODEL_FAMILY,
    Case,
)
from biophysevo.quality.validate_units import normalize as _normalize_unit


TEMPLATE_MARKER = "[template - needs expert review]"


_BINDING_METRICS = {"Kd", "Ki", "IC50", "EC50"}
_KINETIC_METRICS = {"kcat", "Km", "kcat_over_Km", "Vmax"}
_STABILITY_METRICS = {"Tm", "ΔΔG", "DDG", "ddG", "ΔG_folding", "DeltaG_folding"}


# Default physical-model scaffolds per domain. Equation latex matches the
# revision-v2 example block (L160-173). Content is templated, not invented.
_DOMAIN_MODEL_DEFAULTS: dict[str, dict[str, Any]] = {
    "protein_ligand_binding": {
        "model_name": "standard_binding_free_energy",
        "equation_latex": r"\Delta G^\circ = R T \ln K_d",
    },
    "enzyme_kinetics": {
        "model_name": "michaelis_menten",
        "equation_latex": r"v = \frac{V_{\max}[S]}{K_M + [S]}",
    },
    "protein_stability_thermodynamics": {
        "model_name": "two_state_folding",
        "equation_latex": r"K = e^{-\Delta G / RT}",
    },
    "conformational_dynamics_allostery": {
        "model_name": "two_state_conformational_equilibrium",
        "equation_latex": r"K_{eq} = e^{-\Delta G_{conf} / RT}",
    },
    "biomolecular_phase_separation": {
        "model_name": "flory_huggins_phase_separation",
        "equation_latex": r"\Delta G_{mix} = RT(\phi \ln \phi + (1-\phi)\ln(1-\phi) + \chi \phi (1-\phi))",
    },
    "systems_biology_dynamics": {
        "model_name": "mass_action_ode_dynamics",
        "equation_latex": r"\frac{d[X]}{dt} = f([X]; \theta)",
    },
}


_DOMAIN_RESEARCH_QUESTIONS: dict[str, str] = {
    "protein_ligand_binding": "What is the binding affinity of the ligand for the target, and what does it imply for the binding mechanism?",
    "enzyme_kinetics": "What are the catalytic parameters and what do they imply for the catalytic mechanism?",
    "protein_stability_thermodynamics": "How does the mutation alter folding stability, and what does it imply for protein function?",
    "conformational_dynamics_allostery": "How do conformational dynamics couple to the allosteric/functional response?",
    "biomolecular_phase_separation": "What governs the saturation concentration / phase behavior, and what does it imply for condensate formation?",
    "systems_biology_dynamics": "What dynamical regime does the pathway exhibit, and what mechanism produces it?",
}


_DOMAIN_REASONING_SKILLS: dict[str, list[str]] = {
    "protein_ligand_binding": [
        "unit normalization",
        "thermodynamic directionality",
        "free-energy interpretation",
        "evidence-grounded mechanism reasoning",
        "next-experiment design",
    ],
    "enzyme_kinetics": [
        "unit normalization",
        "enzyme kinetic interpretation",
        "structure-function reasoning",
        "evidence-grounded mechanism reasoning",
        "next-experiment design",
    ],
    "protein_stability_thermodynamics": [
        "unit normalization",
        "folding stability interpretation",
        "thermodynamic directionality",
        "structure-function reasoning",
        "evidence-grounded mechanism reasoning",
        "next-experiment design",
    ],
    "conformational_dynamics_allostery": [
        "unit normalization",
        "conformational-equilibrium interpretation",
        "allosteric coupling reasoning",
        "evidence-grounded mechanism reasoning",
        "next-experiment design",
    ],
    "biomolecular_phase_separation": [
        "unit normalization",
        "phase-behavior interpretation",
        "thermodynamics of mixing reasoning",
        "evidence-grounded mechanism reasoning",
        "next-experiment design",
    ],
    "systems_biology_dynamics": [
        "unit normalization",
        "dynamical-systems interpretation",
        "pathway/feedback reasoning",
        "evidence-grounded mechanism reasoning",
        "next-experiment design",
    ],
}


_DOMAIN_MECHANISM_TYPES: dict[str, str] = {
    "protein_ligand_binding": "protein_ligand_binding_mechanism",
    "enzyme_kinetics": "catalytic_mechanism",
    "protein_stability_thermodynamics": "mutation_to_function_mechanism",
    "conformational_dynamics_allostery": "allosteric_mechanism",
    "biomolecular_phase_separation": "condensate_formation_mechanism",
    "systems_biology_dynamics": "pathway_dynamics_mechanism",
}


def _classify_domain(measurements: list[dict]) -> str:
    """Route candidates to one of the 3 v1 domains.

    Priority: stability metrics > kinetic metrics > binding metrics. This
    matches the revision-v2 v1 scope where the three bridge paradigms are
    distinct; ``mixed`` is no longer a valid domain.
    """
    metrics = {m.get("metric") for m in measurements}
    if metrics & _STABILITY_METRICS:
        return "protein_stability_thermodynamics"
    if metrics & _KINETIC_METRICS:
        return "enzyme_kinetics"
    return "protein_ligand_binding"


def _bridge_type_for(domain: str) -> str:
    try:
        return DOMAIN_BRIDGE_COMPATIBILITY[domain]
    except KeyError as exc:
        raise ValueError(f"No bridge_type mapping for domain {domain!r}") from exc


def _templated_physical_interpretation(domain: str, primary: dict) -> dict:
    return {
        "derived_quantity": None,
        "directionality": (
            f"{TEMPLATE_MARKER} regex builder extracted {primary['metric']} "
            f"= {primary['value']} {primary['unit']}; directionality requires "
            "expert review."
        ),
        "consistency_check": (
            f"{TEMPLATE_MARKER} physical consistency vs. the {domain} model "
            "must be confirmed against assay conditions."
        ),
        "caveats": [
            "regex-extracted; expert review pending",
            "assay conditions and model assumptions not verified",
        ],
    }


def _templated_biological_mechanism(domain: str) -> dict:
    return {
        "mechanism_type": _DOMAIN_MECHANISM_TYPES[domain],
        "description": (
            f"{TEMPLATE_MARKER} biological mechanism interpretation for "
            f"{domain} requires expert/LLM review of the source evidence."
        ),
        "structure_function_link": None,
        "mutation_or_ligand_effect": None,
    }


def _nonempty_str(v: Any) -> str | None:
    return v if isinstance(v, str) and v.strip() else None


def _opt_str(v: Any) -> str | None:
    return v if isinstance(v, str) and v.strip() else None


def _sanitize_physical_interpretation(pi: Any) -> dict | None:
    """Return a schema-valid physical_interpretation from LLM output, or None
    if the required string fields are missing/wrong-typed (caller templates)."""
    if not isinstance(pi, dict):
        return None
    directionality = _nonempty_str(pi.get("directionality"))
    consistency = _nonempty_str(pi.get("consistency_check"))
    if not directionality or not consistency:
        return None
    caveats_raw = pi.get("caveats")
    caveats = [c for c in caveats_raw if isinstance(c, str)] if isinstance(caveats_raw, list) else []
    return {
        "derived_quantity": _opt_str(pi.get("derived_quantity")),
        "directionality": directionality,
        "consistency_check": consistency,
        "caveats": caveats,
    }


def _sanitize_biological_mechanism(bm: Any) -> dict | None:
    """Return a schema-valid biological_mechanism from LLM output, or None."""
    if not isinstance(bm, dict):
        return None
    mechanism_type = _nonempty_str(bm.get("mechanism_type"))
    description = _nonempty_str(bm.get("description"))
    if not mechanism_type or not description:
        return None
    return {
        "mechanism_type": mechanism_type,
        "description": description,
        "structure_function_link": _opt_str(bm.get("structure_function_link")),
        "mutation_or_ligand_effect": _opt_str(bm.get("mutation_or_ligand_effect")),
    }


def build_case_from_candidate(
    candidate: dict,
    *,
    case_id: str,
    source: dict[str, Any] | None = None,
    mineru_artifact_path: str | None = None,
    llm_fields: dict | None = None,
) -> dict[str, Any] | None:
    """Convert one extracted candidate doc into a Case dict.

    Returns ``None`` if there is no quantitative evidence linked to an
    evidence_id - without grounded measurements we have no case to build.

    When ``llm_fields`` is provided (evidence-only LLM output, already validated
    against the doc's evidence_ids), its ``quantitative_evidence`` supplies the
    measurements and its ``domain`` / interpretation / mechanism fields override
    the regex defaults and template stubs.
    """
    blocks = candidate.get("evidence_blocks", []) or []

    if llm_fields and llm_fields.get("quantitative_evidence"):
        measurements = []
        for row in llm_fields["quantitative_evidence"]:
            norm = _normalize_unit(row["metric"], float(row["value"]), row["unit"])
            measurements.append(
                {
                    "metric": row["metric"],
                    "value": float(row["value"]),
                    "unit": row["unit"],
                    "normalized_value": norm.normalized_value,
                    "normalized_unit": norm.normalized_unit,
                    "evidence_id": row["evidence_id"],
                    "condition": row.get("condition"),
                }
            )
    else:
        measurements = [
            m for m in candidate.get("measurements", []) if m.get("evidence_id")
        ]

    if not measurements or not blocks:
        return None

    valid_domains = set(DOMAIN_BRIDGE_COMPATIBILITY)
    domain = (llm_fields or {}).get("domain")
    if domain not in valid_domains:
        domain = _classify_domain(measurements)
    bridge_type = _bridge_type_for(domain)
    entities = candidate.get("entities", {}) or {}

    evidence = []
    for b in blocks:
        eid = b.get("evidence_id")
        if not eid:
            continue
        modality = b.get("modality", "text")
        if modality not in {"text", "table", "formula", "figure", "caption", "other"}:
            modality = "other"
        evidence.append(
            {
                "evidence_id": eid,
                "modality": modality,
                "text": b.get("text") or "",
                "source_location": b.get("source_location") or {},
                "mineru_artifact_path": mineru_artifact_path,
            }
        )

    qe = []
    for m in measurements:
        qe.append(
            {
                "metric": m["metric"],
                "value": float(m["value"]),
                "unit": m["unit"],
                "normalized_value": m.get("normalized_value"),
                "normalized_unit": m.get("normalized_unit"),
                "condition": m.get("condition"),
                "evidence_id": m["evidence_id"],
            }
        )

    lf = llm_fields or {}
    primary = measurements[0]
    primary_eid = primary["evidence_id"]
    gold = lf.get("gold_answer") or (
        f"From {primary['metric']} = {primary['value']} {primary['unit']} "
        f"({primary.get('normalized_value')} {primary.get('normalized_unit')}), "
        "design a follow-up experiment to confirm the binding or kinetic mechanism."
    )
    supporting_eids = [
        i for i in (lf.get("supporting_evidence_ids") or []) if i
    ] or [primary_eid]
    research_question = lf.get("research_question") or _DOMAIN_RESEARCH_QUESTIONS[domain]

    pi = _sanitize_physical_interpretation(lf.get("physical_interpretation"))
    physical_interpretation = pi or _templated_physical_interpretation(domain, primary)
    bm = _sanitize_biological_mechanism(lf.get("biological_mechanism"))
    biological_mechanism = bm or _templated_biological_mechanism(domain)

    trajectory = [
        {
            "step_id": "step_001",
            "stage": "research_question",
            "description": research_question,
            "input_evidence_ids": [],
        },
        {
            "step_id": "step_002",
            "stage": "quantitative_observation",
            "description": (
                f"Measured {primary['metric']} = {primary['value']} {primary['unit']}."
            ),
            "input_evidence_ids": [primary_eid],
        },
        {
            "step_id": "step_003",
            "stage": "biophysical_interpretation",
            "description": (
                "Normalized value derived; interpretation grounded in evidence."
            ),
            "input_evidence_ids": [primary_eid],
        },
    ]

    formulas = candidate.get("formulas", []) or []
    model_defaults = _DOMAIN_MODEL_DEFAULTS[domain]
    biophysical_model = {
        "model_name": model_defaults["model_name"],
        "model_family": DOMAIN_DEFAULT_MODEL_FAMILY[domain],
        "secondary_model_families": [],
        "equation_latex": (
            formulas[0].get("latex") if formulas else model_defaults["equation_latex"]
        ),
        "variables": {},
        "assumptions": [],
        "validity_conditions": [],
    }

    case = {
        "case_id": case_id,
        "dataset_type": "Sci-Evo",
        "dataset_family": "Biophys-Bridge",
        "dataset_subtype": "Sci-Evo",
        "bridge_type": bridge_type,
        "domain": domain,
        "source": source
        or {"license": "unknown", "mineru_parse_id": candidate.get("doc_id")},
        "scientific_object": {
            "uniprot_id": (entities.get("uniprot_ids") or [None])[0],
            "pdb_ids": entities.get("pdb_ids", []),
            "enzyme_ec_number": (entities.get("ec_numbers") or [None])[0],
            "mutation": (entities.get("mutations") or [None])[0],
        },
        "research_question": research_question,
        "hypothesis": None,
        "methods": [],
        "quantitative_evidence": qe,
        "biophysical_model": biophysical_model,
        "physical_interpretation": physical_interpretation,
        "biological_mechanism": biological_mechanism,
        "sci_evo_trajectory": trajectory,
        "failure_or_revision": None,
        "agent_tasks": [
            {
                "task_type": "next_experiment_design",
                "input": (
                    f"Given {primary['metric']} = {primary['value']} {primary['unit']}, "
                    "propose the next experiment."
                ),
                "gold_answer": gold,
                "supporting_evidence_ids": supporting_eids,
                "required_reasoning_skills": _DOMAIN_REASONING_SKILLS[domain],
                "allowed_tools": ["MinerU parsed paper"],
            }
        ],
        "evidence": evidence,
        "quality": {
            "schema_valid": True,
            "has_quantitative_evidence": True,
            "has_source_trace": bool(source and source.get("license")),
            "has_mineru_artifact": mineru_artifact_path is not None,
            # Regex-built cases always require expert review before release
            # because the physics/biology templates are stubs, not grounded science.
            "manual_review_status": "needs_fix",
            "score": 0.4,
        },
    }

    Case.model_validate(case)
    return case


def build_cases(
    candidates: Iterable[dict],
    *,
    case_id_prefix: str = "biophysevo_",
) -> Iterable[dict]:
    for i, c in enumerate(candidates, start=1):
        case_id = f"{case_id_prefix}{i:06d}"
        out = build_case_from_candidate(
            c,
            case_id=case_id,
            source={
                "license": c.get("license", "unknown"),
                "mineru_parse_id": c.get("doc_id"),
                "paper_title": c.get("paper_title"),
                "doi": c.get("doi"),
                "pmcid": c.get("pmcid"),
            },
            mineru_artifact_path=c.get("mineru_artifact_path"),
        )
        if out is not None:
            yield out
