"""domain and bridge_type must be a compatible pair (revision-v2 section 150-156)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from biophysevo.schemas.case_schema import (
    DOMAIN_BRIDGE_COMPATIBILITY,
    DOMAIN_DEFAULT_MODEL_FAMILY,
    Case,
)


def test_all_v1_domain_bridge_pairs_validate(make_case):
    """Every documented pair in the compatibility map round-trips."""
    for domain, bridge_type in DOMAIN_BRIDGE_COMPATIBILITY.items():
        case = make_case(domain=domain, bridge_type=bridge_type)
        case["biophysical_model"]["model_family"] = DOMAIN_DEFAULT_MODEL_FAMILY[domain]
        Case.model_validate(case)


def test_mismatched_domain_bridge_pair_rejected(make_case):
    bad = make_case(
        domain="enzyme_kinetics",
        bridge_type="binding_thermodynamics_to_binding_mechanism",
    )
    with pytest.raises(ValidationError, match="bridge_type"):
        Case.model_validate(bad)


def test_compatibility_map_has_all_v1_domains():
    """Sanity check that the map covers the six declared domains."""
    expected = {
        "protein_ligand_binding",
        "enzyme_kinetics",
        "protein_stability_thermodynamics",
        "conformational_dynamics_allostery",
        "biomolecular_phase_separation",
        "systems_biology_dynamics",
    }
    assert set(DOMAIN_BRIDGE_COMPATIBILITY) == expected
