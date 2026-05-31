"""Deterministic physics-consistency checks (non-LLM, reproducible).

Implements three families of relations. ``check_case`` runs every applicable
relation against a case and returns an aggregate dict with the per-relation
``checks`` list and a top-level ``status``.

Relations:
  1. ``dG = RT ln(K)`` — binding free energy vs Kd/Ki/IC50 (Cheng-Prusoff
     approx for IC50; T from ``condition`` or 298.15 K). Inconsistent when
     |ΔG_pred − ΔG_reported| > ``tolerance_kcal``.
  2. ``Eyring: dG‡ = RT ln(k_B·T / (h·kcat))`` — sanity range derived from
     kcat alone (no need for a reported ΔG‡). Flags impossible turnovers
     (ΔG‡ outside 4–35 kcal/mol) as inconsistent; in-range as consistent.
  3. ``van't Hoff at Tm: Tm = ΔH_unf / ΔS_unf`` — fires only when all three
     are reported. Tolerance defaults to 5 K.

Back-compat: callers that previously read flat fields from ``check_case``
(``status``, ``predicted_kcal_per_mol``, …) keep working when exactly one
relation fires — those fields are mirrored at the top level. When 0 fire,
``check_case`` returns ``None``.
"""
from __future__ import annotations

import math
import re
from typing import Any

import pint

_UREG = pint.UnitRegistry()
_R_KCAL = 1.987204259e-3  # kcal/(mol·K)
_KB = 1.380649e-23  # J/K
_H = 6.62607015e-34  # J·s
_KB_OVER_H = _KB / _H  # Hz/K
_DEFAULT_T = 298.15
_EYRING_LOW_KCAL = 4.0    # below this → impossibly fast (likely a diffusion-limit, not catalysis)
_EYRING_HIGH_KCAL = 35.0  # above this → kcat would be essentially zero

_DG_TOKENS = ("binding free energy", "delta g", "deltag", "gibbs", "free energy", "δg", "dg")
_KD_TOKENS = ("kd", "dissociation constant")
_INHIB_TOKENS = ("ki", "ic50", "ec50", "inhibition constant")
_KCAT_TOKENS = ("kcat", "k_cat", "catalytic rate", "turnover number")
_DGACT_TOKENS = ("dg‡", "delta g‡", "activation free energy", "free-energy barrier", "free energy barrier", "δg‡", "dg‡")
_TM_TOKENS = ("melting temperature", "tm", "t_m")
_DH_UNF_TOKENS = ("enthalpy of unfolding", "δh_unf", "delta h unfolding", "δh unfolding", "δh", "delta h")
_DS_UNF_TOKENS = ("entropy of unfolding", "δs_unf", "delta s unfolding", "δs unfolding", "δs", "delta s")


def _matches(metric: str, tokens: tuple[str, ...]) -> bool:
    m = (metric or "").lower()
    return any(tok in m for tok in tokens)


def _find(qe: list[dict], tokens: tuple[str, ...]) -> dict | None:
    return next((q for q in qe if _matches(q.get("metric", ""), tokens)), None)


def _to_molar(value: float, unit: str) -> float | None:
    try:
        return (value * _UREG(unit)).to("molar").magnitude
    except Exception:  # noqa: BLE001
        return None


def _to_kcal_per_mol(value: float, unit: str) -> float | None:
    u = (unit or "").replace("kcal/mol", "kcal/mole").replace("kJ/mol", "kJ/mole")
    try:
        return (value * _UREG(u)).to("kcal/mole").magnitude
    except Exception:  # noqa: BLE001
        return None


def _to_per_second(value: float, unit: str) -> float | None:
    try:
        return (value * _UREG(unit or "1/second")).to("1/second").magnitude
    except Exception:  # noqa: BLE001
        return None


def _to_kelvin(value: float, unit: str) -> float | None:
    u = (unit or "kelvin").lower()
    if u in ("k", "kelvin"):
        return float(value)
    if u in ("degc", "deg c", "°c", "celsius", "c"):
        return float(value) + 273.15
    try:
        return (value * _UREG(u)).to("kelvin").magnitude
    except Exception:  # noqa: BLE001
        return None


def _to_cal_per_mol_K(value: float, unit: str) -> float | None:
    u = (unit or "").replace("/mol", "/mole")
    try:
        return (value * _UREG(u)).to("cal/(mole*kelvin)").magnitude
    except Exception:  # noqa: BLE001
        return None


def _temperature_K(conditions: list[str]) -> float:
    for c in conditions:
        if not c:
            continue
        mk = re.search(r"(\d+(?:\.\d+)?)\s*K\b", c)
        if mk:
            return float(mk.group(1))
        mc = re.search(r"(\d+(?:\.\d+)?)\s*(?:°\s*C|degC|deg C|℃)", c)
        if mc:
            return float(mc.group(1)) + 273.15
    return _DEFAULT_T


def _check_dG_K(qe: list[dict], *, tolerance_kcal: float) -> dict | None:
    """ΔG = RT·ln(K). K is Kd preferred, else Ki/IC50/EC50 (Cheng-Prusoff approx)."""
    k_q = _find(qe, _KD_TOKENS) or _find(qe, _INHIB_TOKENS)
    dg = _find(qe, _DG_TOKENS)
    if not k_q or not dg:
        return None
    k_molar = _to_molar(float(k_q["value"]), k_q.get("unit", ""))
    dg_reported = _to_kcal_per_mol(float(dg["value"]), dg.get("unit", ""))
    if k_molar is None or k_molar <= 0 or dg_reported is None:
        return {
            "relation": "dG = RT ln(K)", "status": "not_checked",
            "assumptions": ["unit conversion failed"],
        }
    T = _temperature_K([k_q.get("condition") or "", dg.get("condition") or ""])
    predicted = _R_KCAL * T * math.log(k_molar)
    residual = abs(predicted - dg_reported)
    status = "consistent" if residual <= tolerance_kcal else "inconsistent"
    used = "Kd" if _matches(k_q.get("metric", ""), _KD_TOKENS) else "IC50/Ki (Cheng-Prusoff approx)"
    return {
        "relation": "dG = RT ln(K)",
        "temperature_K": T,
        "predicted_kcal_per_mol": round(predicted, 3),
        "reported_kcal_per_mol": round(dg_reported, 3),
        "residual_kcal_per_mol": round(residual, 3),
        "tolerance_kcal_per_mol": tolerance_kcal,
        "status": status,
        "assumptions": [
            f"standard state 1 M; T={T} K",
            f"K interpreted as {used}",
        ],
    }


def _check_Eyring_kcat(qe: list[dict], *, low: float = _EYRING_LOW_KCAL,
                       high: float = _EYRING_HIGH_KCAL) -> dict | None:
    """ΔG‡ derived from kcat (Eyring); sanity-range gate (no reported ΔG‡ needed)."""
    kcat_q = _find(qe, _KCAT_TOKENS)
    if not kcat_q:
        return None
    kcat = _to_per_second(float(kcat_q["value"]), kcat_q.get("unit", ""))
    if kcat is None or kcat <= 0:
        return {"relation": "Eyring: dG‡ from kcat", "status": "not_checked",
                "assumptions": ["unit conversion failed"]}
    T = _temperature_K([kcat_q.get("condition") or ""])
    # ΔG‡ = RT · ln(k_B T / h kcat)   [kcal/mol]
    dG_act = _R_KCAL * T * math.log(_KB_OVER_H * T / kcat)
    in_range = low <= dG_act <= high
    out: dict[str, Any] = {
        "relation": "Eyring: dG‡ from kcat",
        "temperature_K": T,
        "derived_dG_act_kcal_per_mol": round(dG_act, 3),
        "sanity_range_kcal_per_mol": [low, high],
        "status": "consistent" if in_range else "inconsistent",
        "assumptions": [
            f"T={T} K; transmission coefficient κ=1",
            "kcat treated as the rate-limiting forward rate",
        ],
    }
    # If the paper also reports an activation free energy, cross-check.
    dG_q = _find(qe, _DGACT_TOKENS)
    if dG_q:
        rep = _to_kcal_per_mol(float(dG_q["value"]), dG_q.get("unit", ""))
        if rep is not None:
            out["reported_dG_act_kcal_per_mol"] = round(rep, 3)
            out["residual_kcal_per_mol"] = round(abs(dG_act - rep), 3)
            if abs(dG_act - rep) > 3.0:
                out["status"] = "inconsistent"
    return out


def _check_Tm_vanthoff(qe: list[dict], *, tolerance_Tm_K: float = 5.0) -> dict | None:
    """Tm = ΔH_unf / ΔS_unf. Fires only when all three reported."""
    tm_q = _find(qe, _TM_TOKENS)
    dh_q = _find(qe, _DH_UNF_TOKENS)
    ds_q = _find(qe, _DS_UNF_TOKENS)
    if not tm_q or not dh_q or not ds_q:
        return None
    Tm = _to_kelvin(float(tm_q["value"]), tm_q.get("unit", ""))
    dH_kcal = _to_kcal_per_mol(float(dh_q["value"]), dh_q.get("unit", ""))
    dS_cal = _to_cal_per_mol_K(float(ds_q["value"]), ds_q.get("unit", ""))
    if Tm is None or dH_kcal is None or dS_cal is None or dS_cal == 0:
        return {"relation": "vant Hoff at Tm: Tm = dH/dS", "status": "not_checked",
                "assumptions": ["unit conversion failed"]}
    predicted_Tm_K = (dH_kcal * 1000.0) / dS_cal  # kcal→cal, then K
    residual = abs(predicted_Tm_K - Tm)
    status = "consistent" if residual <= tolerance_Tm_K else "inconsistent"
    return {
        "relation": "vant Hoff at Tm: Tm = dH/dS",
        "predicted_Tm_K": round(predicted_Tm_K, 2),
        "reported_Tm_K": round(Tm, 2),
        "residual_K": round(residual, 2),
        "tolerance_K": tolerance_Tm_K,
        "status": status,
        "assumptions": ["two-state unfolding; ΔH, ΔS treated as Tm-evaluated"],
    }


def check_case(
    case: dict[str, Any],
    *,
    tolerance_kcal: float = 2.0,
    tolerance_Tm_K: float = 5.0,
) -> dict | None:
    qe = case.get("quantitative_evidence", []) or []
    if not qe:
        return None
    checks: list[dict] = []
    for fn in (
        lambda: _check_dG_K(qe, tolerance_kcal=tolerance_kcal),
        lambda: _check_Eyring_kcat(qe),
        lambda: _check_Tm_vanthoff(qe, tolerance_Tm_K=tolerance_Tm_K),
    ):
        try:
            c = fn()
        except Exception:  # noqa: BLE001 - never let a single relation crash the audit
            c = None
        if c is not None:
            checks.append(c)
    if not checks:
        return None
    statuses = {c.get("status") for c in checks}
    if "inconsistent" in statuses:
        agg = "inconsistent"
    elif "consistent" in statuses:
        agg = "consistent"
    else:
        agg = "not_checked"
    # Back-compat: when exactly one relation fired, mirror its fields at top-level
    # so existing callers (export_release, sci_evo_view, enrich_cases) see the
    # familiar flat shape.
    if len(checks) == 1:
        out = dict(checks[0])
        out["checks"] = checks
        out["status"] = agg
        return out
    return {"status": agg, "checks": checks}
