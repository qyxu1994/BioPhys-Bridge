"""Unit normalization for binding/kinetics metrics via pint."""

from __future__ import annotations

from dataclasses import dataclass

from pint import UnitRegistry

_UREG = UnitRegistry()
# Allow common scientific spellings.
_UREG.define("micromolar = 1e-6 * mol / liter = uM = µM = μM")
_UREG.define("nanomolar = 1e-9 * mol / liter = nM")
_UREG.define("millimolar = 1e-3 * mol / liter = mM")
_UREG.define("molar = mol / liter = M")


@dataclass
class NormalizedMeasurement:
    metric: str
    value: float
    unit: str
    normalized_value: float
    normalized_unit: str


_CONCENTRATION_METRICS = {"Kd", "Ki", "IC50", "EC50", "Km"}
_ENERGY_METRICS = {"deltaG", "ddG"}
_RATE_METRICS = {"kcat"}


def normalize(metric: str, value: float, unit: str) -> NormalizedMeasurement:
    """Convert ``value`` in ``unit`` to a canonical unit per metric family."""
    target: str
    if metric in _CONCENTRATION_METRICS:
        target = "M"
    elif metric in _ENERGY_METRICS:
        target = "kcal/mol"
    elif metric in _RATE_METRICS:
        target = "1/s"
    else:
        return NormalizedMeasurement(metric, value, unit, value, unit)

    try:
        quantity = (value * _UREG(unit)).to(target)
        return NormalizedMeasurement(
            metric=metric,
            value=value,
            unit=unit,
            normalized_value=float(quantity.magnitude),
            normalized_unit=target,
        )
    except Exception:
        return NormalizedMeasurement(metric, value, unit, value, unit)
