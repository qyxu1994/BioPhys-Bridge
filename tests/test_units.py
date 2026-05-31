"""Unit normalization round-trips for nM/uM/mM/M and energy/rate units."""

from __future__ import annotations

import pytest

from biophysevo.quality.validate_units import normalize


@pytest.mark.parametrize(
    "value, unit, expected_M",
    [
        (1.0, "nM", 1e-9),
        (1.0, "uM", 1e-6),
        (1.0, "µM", 1e-6),
        (1.0, "μM", 1e-6),
        (1.0, "mM", 1e-3),
        (1.0, "M", 1.0),
        (500.0, "nM", 5e-7),
    ],
)
def test_concentration_normalization(value, unit, expected_M):
    n = normalize("Kd", value, unit)
    assert n.normalized_unit == "M"
    assert n.normalized_value == pytest.approx(expected_M, rel=1e-9)


def test_kcat_normalization_to_per_second():
    n = normalize("kcat", 60.0, "1/min")
    assert n.normalized_unit == "1/s"
    assert n.normalized_value == pytest.approx(1.0)


def test_unknown_unit_returns_passthrough():
    n = normalize("Kd", 1.0, "not_a_unit")
    assert n.normalized_unit == "not_a_unit"
    assert n.normalized_value == 1.0
