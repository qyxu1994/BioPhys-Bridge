"""The data card is generated from the shipped cases and must be accurate."""
from biophysevo.export_release import render_data_card


def _rec(case_id, domain, title, doi, lic, nqe=3):
    return {
        "case_id": case_id, "domain": domain,
        "source": {"paper_title": title, "doi": doi, "license": lic},
        "quantitative_evidence": [{"metric": "x"}] * nqe,
    }


def _metrics():
    return {
        "n_valid": 2, "schema_valid_rate": 1.0, "quantitative_evidence_rate": 1.0,
        "unit_normalization_success_rate": 1.0, "source_license_coverage": 1.0,
        "evidence_coverage_rate": 1.0, "sci_evo_completeness_score": 0.4286,
    }


def test_data_card_reflects_actual_domains_and_provenance():
    recs = [
        _rec("c1", "biomolecular_phase_separation", "Phase paper", "10.1/x", "CC-BY-4.0"),
        _rec("c2", "systems_biology_dynamics", "Systems paper", "10.2/y", "CC0-1.0"),
    ]
    card = render_data_card(recs, _metrics())
    # actual domains present, with counts
    assert "biomolecular_phase_separation" in card
    assert "systems_biology_dynamics" in card
    # provenance rows
    assert "Phase paper" in card and "10.1/x" in card and "CC-BY-4.0" in card
    assert "Systems paper" in card and "CC0-1.0" in card
    # honest methodology
    assert "gpt-4o" in card and "evidence_id" in card
    # the old false claim must NOT be present
    assert "disabled by default" not in card
    # must not assert enzyme_kinetics coverage when absent
    assert "enzyme_kinetics" not in card
