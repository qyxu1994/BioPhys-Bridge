"""All 6 v1 domains must have complete builder lookup entries."""
from biophysevo.schemas.case_schema import DOMAIN_BRIDGE_COMPATIBILITY
from biophysevo.extraction import sci_evo_builder as B


def test_all_six_domains_have_lookup_entries():
    domains = set(DOMAIN_BRIDGE_COMPATIBILITY)
    assert len(domains) == 6
    for d in domains:
        assert d in B._DOMAIN_MODEL_DEFAULTS, f"missing model default: {d}"
        assert "model_name" in B._DOMAIN_MODEL_DEFAULTS[d]
        assert "equation_latex" in B._DOMAIN_MODEL_DEFAULTS[d]
        assert d in B._DOMAIN_RESEARCH_QUESTIONS
        assert d in B._DOMAIN_REASONING_SKILLS and B._DOMAIN_REASONING_SKILLS[d]
        assert d in B._DOMAIN_MECHANISM_TYPES
