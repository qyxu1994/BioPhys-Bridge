import json

from biophysevo.extraction import enrich_case as E


class _FakeClient:
    def __init__(self, content):
        self._c = content
        self.chat = self

    @property
    def completions(self):
        return self

    def create(self, **kw):
        msg = type("M", (), {"content": self._c})
        ch = type("C", (), {"message": msg})
        return type("R", (), {"choices": [ch]})


def _case():
    return {
        "evidence": [{"evidence_id": "e1", "modality": "table", "text": "Kd=14 nM"}],
        "quantitative_evidence": [{"metric": "Kd", "value": 14.0, "unit": "nM", "evidence_id": "e1"}],
        # legacy singular field from pre-migration cases; enrichment must drop it
        "agent_task": {"task_type": "next_experiment_design", "input": "x", "gold_answer": "y",
                       "supporting_evidence_ids": ["e1"]},
    }


def _llm_payload():
    return json.dumps({
        "sci_evo_trajectory": [
            {"step_id": 1, "stage": "research_question", "description": "q",
             "input_evidence_ids": [], "reasoning": "why", "output": None},
            {"step_id": 2, "stage": "quantitative_observation", "description": "obs",
             "input_evidence_ids": ["e1", "e_FAKE"], "reasoning": "r", "output": "o"},
            {"step_id": 3, "stage": "failure_or_revision", "description": "bad extras",
             "input_evidence_ids": ["e1"], "reasoning": "r", "output": "o",
             "evidence_ids": ["e1"], "revision_decision": "extra"},
        ],
        "biophysical_model": {"model_name": "standard_binding_free_energy",
            "model_family": "binding_thermodynamics",
            "equation_latex": "\\Delta G = RT \\ln K_d", "variables": {"K_d": "dissociation constant"},
            "assumptions": ["two-state"], "validity_conditions": ["dilute"]},
        "physical_interpretation": {"derived_quantity": "DeltaG",
            "directionality": "Lower Kd means tighter binding.",
            "consistency_check": "Kd and DeltaG direction agree.", "caveats": ["assay-specific"]},
        "biological_mechanism": {"mechanism_type": "protein_ligand_binding_mechanism",
            "description": "Tight binding supports target engagement.",
            "structure_function_link": "binding site occupancy", "mutation_or_ligand_effect": None},
        "failure_or_revision": {"present": True, "description": "none really", "evidence_ids": ["e_FAKE"]},
        "agent_tasks": [
            {"task_type": "derivation", "input": "compute dG", "gold_answer": "dG=...",
             "supporting_evidence_ids": ["e1"]},
            {"task_type": "mechanism_from_evidence", "input": "infer", "gold_answer": "mech",
             "supporting_evidence_ids": ["e1", "e_FAKE"]},
        ],
    })


def test_enrich_drops_fabricated_ids_and_preserves_quant():
    out = E.enrich_case(_case(), enabled=True, client=_FakeClient(_llm_payload()))
    assert out["quantitative_evidence"] == _case()["quantitative_evidence"]
    s2 = out["sci_evo_trajectory"][1]
    assert s2["input_evidence_ids"] == ["e1"]
    assert out["agent_tasks"][1]["supporting_evidence_ids"] == ["e1"]
    assert out["failure_or_revision"] is None  # only cited e_FAKE -> nulled
    assert len(out["agent_tasks"]) == 2
    assert out["physical_interpretation"]["directionality"].startswith("Lower Kd")
    assert out["biological_mechanism"]["description"].startswith("Tight binding")
    # step_id coerced to string (schema requires str)
    assert all(isinstance(s["step_id"], str) for s in out["sci_evo_trajectory"])
    # legacy singular agent_task removed (schema forbids extras)
    assert "agent_task" not in out
    assert "evidence_ids" not in out["sci_evo_trajectory"][2]


def test_enrich_falls_back_from_incompatible_model_family():
    c = _case()
    c["domain"] = "protein_ligand_binding"
    c["biophysical_model"] = {"model_family": "binding_thermodynamics"}
    payload = json.loads(_llm_payload())
    payload["biophysical_model"]["model_family"] = "mechanical_force_response"
    out = E.enrich_case(c, enabled=True, client=_FakeClient(json.dumps(payload)))
    assert out["biophysical_model"]["model_family"] == "binding_thermodynamics"


def test_enrich_coerces_task_vocab_and_adds_next_step():
    payload = json.loads(_llm_payload())
    payload["sci_evo_trajectory"] = [
        s for s in payload["sci_evo_trajectory"]
        if s["stage"] != "next_step"
    ]
    payload["agent_tasks"][0]["required_reasoning_skills"] = list("bad vocabulary")
    payload["agent_tasks"][0]["allowed_tools"] = "calculator, MinerU parsed paper"
    out = E.enrich_case(_case(), enabled=True, client=_FakeClient(json.dumps(payload)))
    task = out["agent_tasks"][0]
    assert task["required_reasoning_skills"] == [
        "evidence grounding",
        "quantitative model interpretation",
        "mechanism reasoning",
        "next-step design",
    ]
    assert task["allowed_tools"] == ["calculator", "MinerU parsed paper"]
    assert out["sci_evo_trajectory"][-1]["stage"] == "next_step"
    assert out["sci_evo_trajectory"][-1]["input_evidence_ids"] == ["e1"]


def test_enrich_coerces_model_variable_values_to_strings():
    payload = json.loads(_llm_payload())
    payload["biophysical_model"]["variables"]["interacting_residues"] = ["Tyr528", "Trp571"]
    out = E.enrich_case(_case(), enabled=True, client=_FakeClient(json.dumps(payload)))
    assert out["biophysical_model"]["variables"]["interacting_residues"] == '["Tyr528", "Trp571"]'


def test_enrich_disabled_returns_input_unchanged():
    c = _case()
    assert E.enrich_case(c, enabled=False) == c


def test_enrich_prompt_trims_large_evidence_blocks():
    c = _case()
    c["evidence"] = [
        {"evidence_id": f"e{i}", "modality": "text", "text": "background " * 2000}
        for i in range(20)
    ] + [{"evidence_id": "metric", "modality": "table", "text": "Kd = 14 nM " * 2000}]
    messages = E.build_messages(c)
    assert len(messages[1]["content"]) < 120000
    assert "metric" in messages[1]["content"][:2000]
