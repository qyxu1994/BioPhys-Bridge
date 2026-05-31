"""Regex extraction for quantitative measurements (Kd, Ki, IC50, kcat, Km, ...)."""

from __future__ import annotations

import re
from dataclasses import dataclass

METRICS = [
    "Kd",
    "Ki",
    "IC50",
    "EC50",
    "Km",
    "Vmax",
    "kcat",
    "kcat/Km",
    "Tm",
    "deltaG",
    "ddG",
]

_METRIC_PATTERN = r"(?:Kd|Ki|IC50|EC50|Km|Vmax|kcat/Km|kcat|Tm|ΔΔG|ΔG|\\Delta\\Delta\s*G|\\Delta\s*G)"
_NUM = r"(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)"
_PM = r"(?:\s*(?:\+/-|\u00b1|\\pm)\s*\d+(?:\.\d+)?)?"
# Unit token: either ``<digit>/<letters>`` (e.g. 1/s, 1/min) or starts with a
# letter and runs through letters/digits/slash/dash/Greek mu/superscripts.
_UNIT = r"(\d+/[A-Za-z]+|[A-Za-zµμ°][A-Za-z0-9/°·\-²³µμ]*)"

_METRIC_VALUE_RE = re.compile(
    rf"({_METRIC_PATTERN})\s*=?\s*{_NUM}{_PM}\s*({_UNIT})",
    flags=re.UNICODE,
)


@dataclass
class Measurement:
    metric: str
    value: float
    unit: str
    span: tuple[int, int]


def _normalize_metric(raw: str) -> str:
    m = raw.strip()
    table = {
        "ΔG": "deltaG",
        "\\Delta G": "deltaG",
        "ΔΔG": "ddG",
        "\\Delta\\Delta G": "ddG",
        "kcat/Km": "kcat_over_Km",
    }
    return table.get(m, m)


def find_measurements(text: str) -> list[Measurement]:
    out: list[Measurement] = []
    for m in _METRIC_VALUE_RE.finditer(text):
        metric_raw = m.group(1)
        value_str = m.group(2)
        # group(3) is the outer unit group; the inner alternation may set
        # group(4) for "<digit>/letters" or be empty. Take group(3) as the
        # full captured unit token.
        unit = (m.group(3) or "").strip().rstrip(".,;)")
        if not unit:
            continue
        try:
            value = float(value_str)
        except ValueError:
            continue
        out.append(
            Measurement(
                metric=_normalize_metric(metric_raw),
                value=value,
                unit=unit,
                span=m.span(),
            )
        )
    return out
