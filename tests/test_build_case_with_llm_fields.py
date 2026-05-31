from biophysevo.extraction.sci_evo_builder import build_case_from_candidate


def _candidate():
    return {
        "doc_id": "BPB0005_SeqDeterminants_PhaseBehavior",
        "entities": {},
        "measurements": [],  # regex found nothing
        "formulas": [],
        "evidence_blocks": [
            {"evidence_id": "ev_t0001", "modality": "table", "text": "Csat = 2.0 uM",
             "source_location": {"page": 3}},
        ],
    }


def test_llm_fields_drive_domain_and_measurements():
    llm_fields = {
        "domain": "biomolecular_phase_separation",
        "quantitative_evidence": [
            {"metric": "Csat", "value": 2.0, "unit": "uM", "condition": "25 C", "evidence_id": "ev_t0001"},
        ],
        "physical_interpretation": {
            "derived_quantity": "saturation concentration",
            "directionality": "lower Csat means stronger phase separation propensity",
            "consistency_check": "consistent with coarse-grained model predictions",
            "caveats": ["model-dependent"],
        },
        "biological_mechanism": {
            "mechanism_type": "condensate_formation_mechanism",
            "description": "Multivalent contacts drive condensation above Csat.",
            "structure_function_link": None,
            "mutation_or_ligand_effect": None,
        },
        "research_question": "What sets the saturation concentration?",
        "gold_answer": "Csat=2.0 uM implies condensation above that threshold.",
        "supporting_evidence_ids": ["ev_t0001"],
    }
    case = build_case_from_candidate(
        _candidate(), case_id="biophysevo_000001",
        source={"license": "CC0-1.0", "mineru_parse_id": "BPB0005_SeqDeterminants_PhaseBehavior"},
        llm_fields=llm_fields,
    )
    assert case is not None
    assert case["domain"] == "biomolecular_phase_separation"
    assert case["bridge_type"] == "phase_separation_to_condensate_mechanism"
    assert case["quantitative_evidence"][0]["metric"] == "Csat"
    assert "[template" not in case["biological_mechanism"]["description"]
    assert case["quality"]["manual_review_status"] == "needs_fix"


def test_llm_bad_field_types_fall_back_to_template_without_crashing():
    # LLM returned a bool for consistency_check and a non-list caveats; the
    # builder must fall back to the template instead of raising on validation.
    llm_fields = {
        "domain": "protein_ligand_binding",
        "quantitative_evidence": [
            {"metric": "Kd", "value": 120.0, "unit": "nM", "condition": None, "evidence_id": "ev_t0001"},
        ],
        "physical_interpretation": {
            "derived_quantity": "Kd", "directionality": "lower=tighter",
            "consistency_check": True, "caveats": "oops not a list",
        },
        "biological_mechanism": {"mechanism_type": 5, "description": None},
        "supporting_evidence_ids": ["ev_t0001"],
    }
    case = build_case_from_candidate(
        _candidate(), case_id="biophysevo_000001",
        source={"license": "x", "mineru_parse_id": "d"},
        llm_fields=llm_fields,
    )
    assert case is not None
    assert "[template" in case["physical_interpretation"]["consistency_check"]
    assert "[template" in case["biological_mechanism"]["description"]


def test_no_llm_fields_falls_back_to_regex_path_and_drops_when_empty():
    # Without llm_fields and no regex measurements -> dropped (existing behavior).
    assert build_case_from_candidate(
        _candidate(), case_id="biophysevo_000001",
        source={"license": "x", "mineru_parse_id": "d"},
    ) is None
