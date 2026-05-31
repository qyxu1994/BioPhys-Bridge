from biophysevo.extraction.sci_evo_view import to_three_block


def _case():
    return {
        "case_id": "biophysevo_000001",
        "domain": "protein_ligand_binding",
        "bridge_type": "binding_thermodynamics_to_binding_mechanism",
        "research_question": "What is the binding mechanism?",
        "scientific_object": {"uniprot_id": None, "pdb_ids": [], "mutation": None},
        "quantitative_evidence": [{"metric": "Kd", "value": 14.0, "unit": "nM", "evidence_id": "e1"}],
        "sci_evo_trajectory": [{"step_id": "s1", "stage": "research_question", "description": "q",
                                 "input_evidence_ids": [], "reasoning": "r", "output": "o"}],
        "biological_mechanism": {"mechanism_type": "x", "description": "mech"},
        "agent_tasks": [{"task_type": "derivation", "input": "i", "gold_answer": "g",
                         "supporting_evidence_ids": ["e1"]}],
    }


def test_three_block_view_shape():
    v = to_three_block(_case(), {"relation": "dG = RT ln(Kd)", "status": "consistent"})
    assert set(v) >= {"initial_requirement", "design_compute_experiment_trajectory", "success_criteria"}
    assert v["initial_requirement"]["research_question"] == "What is the binding mechanism?"
    assert v["initial_requirement"]["target_metrics"][0]["metric"] == "Kd"
    assert len(v["design_compute_experiment_trajectory"]) == 1
    assert v["success_criteria"]["physics_consistency"]["status"] == "consistent"
    assert v["success_criteria"]["mechanism"] == "mech"


def test_three_block_handles_no_consistency():
    v = to_three_block(_case(), None)
    assert v["success_criteria"]["physics_consistency"] is None
