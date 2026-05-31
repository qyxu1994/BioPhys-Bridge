"""Pydantic v2 models for Biophys-Bridge cases.

Biophys-Bridge is the project umbrella. Sci-Evo is the contest dataset
type: each case is a physics-grounded scientific evolution trajectory.

Hard rules enforced (see implement-plan/revision-v2.md):
- case_id required and regex-validated.
- dataset_type must be "Sci-Evo".
- dataset_family must be "Biophys-Bridge".
- dataset_subtype must be "Sci-Evo".
- domain and bridge_type must be a compatible pair.
- biophysical_model, physical_interpretation, and biological_mechanism are
  required on every Case.
- Every quantitative_evidence item must have evidence_id.
- failure_or_revision.present=True requires evidence_ids or
  inferred_from_discussion=True.
- All numeric metrics preserve original unit and normalized unit.
- Source records must include license metadata.
- gold_answer must be supported by at least one evidence_id.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


CASE_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


Domain = Literal[
    "protein_ligand_binding",
    "enzyme_kinetics",
    "protein_stability_thermodynamics",
    "conformational_dynamics_allostery",
    "biomolecular_phase_separation",
    "systems_biology_dynamics",
]


BridgeType = Literal[
    "binding_thermodynamics_to_binding_mechanism",
    "enzyme_kinetics_to_catalytic_mechanism",
    "folding_stability_thermodynamics_to_mutation_mechanism",
    "conformational_dynamics_to_allosteric_mechanism",
    "phase_separation_to_condensate_mechanism",
    "systems_biology_dynamics_to_pathway_mechanism",
]


PhysicsModelFamily = Literal[
    "binding_thermodynamics",
    "enzyme_reaction_kinetics",
    "folding_stability_thermodynamics",
    "conformational_allostery_energy_landscape",
    "polymer_phase_separation_statistical_mechanics",
    "systems_stochastic_dynamics",
    "mechanical_force_response",
    "spatial_transport_electrostatics",
    "evolutionary_fitness_landscape",
]


# Each domain has exactly one compatible bridge_type in v1.
DOMAIN_BRIDGE_COMPATIBILITY: dict[str, str] = {
    "protein_ligand_binding": "binding_thermodynamics_to_binding_mechanism",
    "enzyme_kinetics": "enzyme_kinetics_to_catalytic_mechanism",
    "protein_stability_thermodynamics": "folding_stability_thermodynamics_to_mutation_mechanism",
    "conformational_dynamics_allostery": "conformational_dynamics_to_allosteric_mechanism",
    "biomolecular_phase_separation": "phase_separation_to_condensate_mechanism",
    "systems_biology_dynamics": "systems_biology_dynamics_to_pathway_mechanism",
}


MODEL_FAMILY_VALUES: set[str] = set(PhysicsModelFamily.__args__)  # type: ignore[attr-defined]


DOMAIN_MODEL_FAMILY_COMPATIBILITY: dict[str, set[str]] = {
    "protein_ligand_binding": {
        "binding_thermodynamics",
        "conformational_allostery_energy_landscape",
        "spatial_transport_electrostatics",
    },
    "enzyme_kinetics": {
        "enzyme_reaction_kinetics",
        "binding_thermodynamics",
        "conformational_allostery_energy_landscape",
        "evolutionary_fitness_landscape",
    },
    "protein_stability_thermodynamics": {
        "folding_stability_thermodynamics",
        "conformational_allostery_energy_landscape",
        "mechanical_force_response",
    },
    "conformational_dynamics_allostery": {
        "conformational_allostery_energy_landscape",
        "binding_thermodynamics",
        "enzyme_reaction_kinetics",
        "mechanical_force_response",
    },
    "biomolecular_phase_separation": {
        "polymer_phase_separation_statistical_mechanics",
        "spatial_transport_electrostatics",
        "systems_stochastic_dynamics",
    },
    "systems_biology_dynamics": {
        "systems_stochastic_dynamics",
        "enzyme_reaction_kinetics",
        "evolutionary_fitness_landscape",
        "spatial_transport_electrostatics",
    },
}


DOMAIN_DEFAULT_MODEL_FAMILY: dict[str, str] = {
    "protein_ligand_binding": "binding_thermodynamics",
    "enzyme_kinetics": "enzyme_reaction_kinetics",
    "protein_stability_thermodynamics": "folding_stability_thermodynamics",
    "conformational_dynamics_allostery": "conformational_allostery_energy_landscape",
    "biomolecular_phase_separation": "polymer_phase_separation_statistical_mechanics",
    "systems_biology_dynamics": "systems_stochastic_dynamics",
}


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_title: str | None = None
    doi: str | None = None
    pmcid: str | None = None
    license: str = Field(..., description="Required license string (e.g., CC-BY-4.0).")
    source_url: str | None = None
    mineru_parse_id: str | None = None
    evidence_completeness: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("license")
    @classmethod
    def _normalize_license(cls, v: str) -> str:
        aliases = {
            "cc by": "CC-BY-4.0",
            "cc-by": "CC-BY-4.0",
            "cc-by-4.0": "CC-BY-4.0",
            "cc by 4.0": "CC-BY-4.0",
            "cc_by_4.0": "CC-BY-4.0",
            "cc0": "CC0-1.0",
            "cc-0": "CC0-1.0",
            "cc0-1.0": "CC0-1.0",
            "cc0 1.0": "CC0-1.0",
        }
        raw = (v or "").strip()
        return aliases.get(raw.lower(), raw)


class ScientificObject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    protein_name: str | None = None
    uniprot_id: str | None = None
    pdb_ids: list[str] = Field(default_factory=list)
    ligand_name: str | None = None
    ligand_smiles: str | None = None
    enzyme_ec_number: str | None = None
    mutation: str | None = None


class Method(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method_type: Literal["wet_lab", "computational", "structural", "in_silico", "other"]
    method_name: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class QuantitativeEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric: str
    value: float
    unit: str
    normalized_value: float | None = None
    normalized_unit: str | None = None
    condition: str | None = None
    evidence_id: str = Field(..., min_length=1)


class BiophysicalModel(BaseModel):
    """Physical/biophysical model behind the quantitative observation.

    Mirrors revision-v2.md "physical_model" block. The wrapper class name stays
    `BiophysicalModel` for backward compatibility, but the sub-fields follow
    the revision wording (`assumptions`, `validity_conditions`).
    """

    model_config = ConfigDict(extra="forbid")

    model_name: str = Field(..., min_length=1)
    model_family: PhysicsModelFamily
    secondary_model_families: list[PhysicsModelFamily] = Field(default_factory=list)
    equation_latex: str | None = None
    variables: dict[str, str] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    validity_conditions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _secondary_families_unique(self) -> "BiophysicalModel":
        if self.model_family in self.secondary_model_families:
            raise ValueError(
                "secondary_model_families must not include the primary model_family."
            )
        if len(set(self.secondary_model_families)) != len(self.secondary_model_families):
            raise ValueError("secondary_model_families must not contain duplicates.")
        return self


class PhysicalInterpretation(BaseModel):
    """Quantitative-to-physical bridge: what does the number mean?"""

    model_config = ConfigDict(extra="forbid")

    derived_quantity: str | None = None
    directionality: str = Field(..., min_length=1)
    consistency_check: str = Field(..., min_length=1)
    caveats: list[str] = Field(default_factory=list)


class BiologicalMechanism(BaseModel):
    """Physical-to-biological bridge: what mechanism does the physics imply?"""

    model_config = ConfigDict(extra="forbid")

    mechanism_type: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    structure_function_link: str | None = None
    mutation_or_ligand_effect: str | None = None


class ExpertAnnotation(BaseModel):
    """Optional curator-supplied reasoning, separate from auto-extraction."""

    model_config = ConfigDict(extra="forbid")

    physics_reasoning: str = Field(..., min_length=1)
    biological_reasoning: str = Field(..., min_length=1)
    uncertainty: str | None = None
    reviewer_notes: str | None = None


class SciEvoStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str
    stage: Literal[
        "research_question",
        "hypothesis",
        "method_design",
        "quantitative_observation",
        "biophysical_interpretation",
        "failure_or_revision",
        "next_step",
    ]
    description: str
    input_evidence_ids: list[str] = Field(default_factory=list)
    reasoning: str | None = None
    output: str | None = None


class FailureOrRevision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    present: bool
    description: str | None = None
    revision_decision: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    inferred_from_discussion: bool = False

    @model_validator(mode="after")
    def _evidence_required_when_present(self) -> "FailureOrRevision":
        if self.present and not self.evidence_ids and not self.inferred_from_discussion:
            raise ValueError(
                "failure_or_revision.present is True but no evidence_ids were "
                "provided and inferred_from_discussion is False."
            )
        return self


class AgentTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_type: str
    input: str
    gold_answer: str
    supporting_evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence IDs that ground the gold_answer.",
    )
    required_reasoning_skills: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)


class SourceLocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int | None = None
    section: str | None = None
    table_id: str | None = None
    figure_id: str | None = None
    paragraph_index: int | None = None


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., min_length=1)
    modality: Literal["text", "table", "formula", "figure", "caption", "other"]
    source_location: SourceLocation = Field(default_factory=SourceLocation)
    text: str | None = None
    mineru_artifact_path: str | None = None


class Quality(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_valid: bool = True
    has_quantitative_evidence: bool = False
    has_source_trace: bool = False
    has_mineru_artifact: bool = False
    manual_review_status: Literal[
        "unreviewed", "reviewed", "needs_fix", "exclude"
    ] = "unreviewed"
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    reviewer_notes: str | None = None


class Case(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(..., min_length=1)
    dataset_type: Literal["Sci-Evo"]
    dataset_family: Literal["Biophys-Bridge"]
    dataset_subtype: Literal["Sci-Evo"]
    bridge_type: BridgeType
    domain: Domain
    source: Source
    scientific_object: ScientificObject
    research_question: str
    hypothesis: str | None = None
    methods: list[Method] = Field(default_factory=list)
    quantitative_evidence: list[QuantitativeEvidence] = Field(default_factory=list)
    biophysical_model: BiophysicalModel
    physical_interpretation: PhysicalInterpretation
    biological_mechanism: BiologicalMechanism
    expert_annotation: ExpertAnnotation | None = None
    sci_evo_trajectory: list[SciEvoStep] = Field(default_factory=list)
    failure_or_revision: FailureOrRevision | None = None
    agent_tasks: list[AgentTask] = Field(..., min_length=1)
    evidence: list[Evidence] = Field(default_factory=list)
    quality: Quality = Field(default_factory=Quality)

    @field_validator("case_id")
    @classmethod
    def _case_id_format(cls, v: str) -> str:
        if not CASE_ID_RE.match(v):
            raise ValueError(
                f"case_id must match {CASE_ID_RE.pattern}; got {v!r}"
            )
        return v

    @model_validator(mode="after")
    def _domain_bridge_compatible(self) -> "Case":
        expected = DOMAIN_BRIDGE_COMPATIBILITY.get(self.domain)
        if expected is None:
            raise ValueError(f"Unknown domain: {self.domain!r}")
        if self.bridge_type != expected:
            raise ValueError(
                f"bridge_type {self.bridge_type!r} is not compatible with "
                f"domain {self.domain!r}; expected {expected!r}."
            )
        return self

    @model_validator(mode="after")
    def _domain_model_family_compatible(self) -> "Case":
        compatible = DOMAIN_MODEL_FAMILY_COMPATIBILITY.get(self.domain, set())
        if self.biophysical_model.model_family not in compatible:
            raise ValueError(
                f"model_family {self.biophysical_model.model_family!r} is not "
                f"compatible with domain {self.domain!r}; expected one of "
                f"{sorted(compatible)!r}."
            )
        return self

    @model_validator(mode="after")
    def _evidence_ids_resolve(self) -> "Case":
        known = {e.evidence_id for e in self.evidence}

        def _check(ids: list[str], where: str) -> None:
            missing = [i for i in ids if i not in known]
            if missing:
                raise ValueError(
                    f"{where} references unknown evidence_id(s): {missing}"
                )

        for qe in self.quantitative_evidence:
            _check([qe.evidence_id], f"quantitative_evidence[{qe.metric}]")
        for step in self.sci_evo_trajectory:
            _check(step.input_evidence_ids, f"sci_evo_trajectory[{step.step_id}]")
        if self.failure_or_revision is not None:
            _check(
                self.failure_or_revision.evidence_ids,
                "failure_or_revision",
            )
        if not self.agent_tasks:
            raise ValueError("agent_tasks must contain at least one task.")
        for i, task in enumerate(self.agent_tasks):
            _check(task.supporting_evidence_ids, f"agent_tasks[{i}]")
            if not task.supporting_evidence_ids:
                raise ValueError(
                    f"agent_tasks[{i}].gold_answer must be supported by at least "
                    "one evidence_id in supporting_evidence_ids."
                )
        return self


def validate_cases(cases: list[dict]) -> list[Case]:
    """Validate raw dicts, also enforcing unique case_id across the batch."""
    parsed = [Case.model_validate(c) for c in cases]
    seen: set[str] = set()
    for c in parsed:
        if c.case_id in seen:
            raise ValueError(f"Duplicate case_id detected: {c.case_id}")
        seen.add(c.case_id)
    return parsed


def emit_json_schema() -> dict:
    return Case.model_json_schema()


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Biophys-Bridge schema utilities.")
    parser.add_argument(
        "--emit-json",
        action="store_true",
        help="Write JSON Schema for Case to schemas/case_schema.json next to this file.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).with_name("case_schema.json"),
        help="Output path for JSON Schema.",
    )
    args = parser.parse_args(argv)

    if args.emit_json:
        schema = emit_json_schema()
        args.out.write_text(json.dumps(schema, indent=2, sort_keys=True))
        print(f"Wrote {args.out}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
