"""Derived 3-block Sci-Evo view (organizers' reference structure).

Pure transform from a Case dict; no schema change. Emitted at release time so
judges see the closed loop: initial_requirement -> trajectory -> success_criteria.
"""
from __future__ import annotations

from typing import Any


def to_three_block(case: dict[str, Any], consistency: dict | None) -> dict[str, Any]:
    qe = case.get("quantitative_evidence", []) or []
    return {
        "case_id": case.get("case_id"),
        "domain": case.get("domain"),
        "bridge_type": case.get("bridge_type"),
        "initial_requirement": {
            "research_question": case.get("research_question"),
            "scientific_object": case.get("scientific_object", {}),
            "hypothesis": case.get("hypothesis"),
            "target_metrics": [
                {"metric": q.get("metric"), "value": q.get("value"), "unit": q.get("unit"),
                 "evidence_id": q.get("evidence_id")}
                for q in qe
            ],
        },
        "design_compute_experiment_trajectory": [
            {
                "step_id": s.get("step_id"),
                "stage": s.get("stage"),
                "reasoning": s.get("reasoning"),
                "action": s.get("description"),
                "observation": s.get("output"),
                "evidence_ids": s.get("input_evidence_ids", []),
            }
            for s in case.get("sci_evo_trajectory", []) or []
        ],
        "success_criteria": {
            "physics_consistency": consistency,
            "mechanism": (case.get("biological_mechanism") or {}).get("description"),
            "agent_tasks": case.get("agent_tasks", []),
        },
    }
