from biophysevo.physics.consistency import check_case


def _case(qe):
    return {"quantitative_evidence": qe}


def test_kd_dG_pair_is_consistent():
    # Kd=14 nM, T=298.15 -> dG = RT ln(Kd[M]) ~ -10.7 kcal/mol; reported -8.46 -> residual ~2.2
    case = _case([
        {"metric": "Kd", "value": 14.0, "unit": "nM", "condition": None, "evidence_id": "e1"},
        {"metric": "binding free energy", "value": -8.46, "unit": "kcal/mol", "condition": None, "evidence_id": "e2"},
    ])
    r = check_case(case, tolerance_kcal=3.0)
    assert r["status"] == "consistent"
    assert abs(r["predicted_kcal_per_mol"] - (-10.7)) < 0.3
    assert abs(r["residual_kcal_per_mol"] - 2.2) < 0.3


def test_inconsistent_when_far_off():
    case = _case([
        {"metric": "Kd", "value": 1.0, "unit": "uM", "evidence_id": "e1"},
        {"metric": "ΔG", "value": -1.0, "unit": "kcal/mol", "evidence_id": "e2"},
    ])
    r = check_case(case, tolerance_kcal=2.0)
    assert r["status"] == "inconsistent"


def test_no_pair_returns_none():
    assert check_case(_case([{"metric": "Tm", "value": 60, "unit": "degC", "evidence_id": "e1"}])) is None


def test_temperature_parsed_from_condition():
    case = _case([
        {"metric": "Kd", "value": 14.0, "unit": "nM", "condition": "measured at 318 K", "evidence_id": "e1"},
        {"metric": "ΔG", "value": -9.0, "unit": "kcal/mol", "evidence_id": "e2"},
    ])
    r = check_case(case)
    assert r["temperature_K"] == 318.0


def test_eyring_kcat_in_typical_range_is_consistent():
    # kcat = 100 /s at 298 K -> dG‡ ~ 14.4 kcal/mol (within 4-35 kcal/mol)
    case = _case([
        {"metric": "kcat", "value": 100.0, "unit": "1/s", "evidence_id": "e1"},
    ])
    r = check_case(case)
    assert r is not None
    assert r["relation"] == "Eyring: dG‡ from kcat"
    assert r["status"] == "consistent"
    # numerical sanity: should land near 14-15 kcal/mol
    assert 13.0 < r["derived_dG_act_kcal_per_mol"] < 16.0


def test_eyring_impossibly_fast_kcat_inconsistent():
    # 10^15 /s exceeds the universal upper bound k_BT/h ≈ 6.2e12 -> dG‡ < 0
    case = _case([
        {"metric": "kcat", "value": 1.0e15, "unit": "1/s", "evidence_id": "e1"},
    ])
    r = check_case(case)
    assert r["status"] == "inconsistent"


def test_ic50_is_used_when_kd_absent():
    case = _case([
        {"metric": "IC50", "value": 14.0, "unit": "nM", "evidence_id": "e1"},
        {"metric": "binding free energy", "value": -10.7, "unit": "kcal/mol", "evidence_id": "e2"},
    ])
    r = check_case(case, tolerance_kcal=1.0)
    assert r["relation"] == "dG = RT ln(K)"
    assert r["status"] == "consistent"


def test_two_relations_aggregate_status():
    # Kd+dG (consistent) AND kcat (consistent) -> aggregate consistent, with checks list
    case = _case([
        {"metric": "Kd", "value": 14.0, "unit": "nM", "evidence_id": "e1"},
        {"metric": "binding free energy", "value": -10.7, "unit": "kcal/mol", "evidence_id": "e2"},
        {"metric": "kcat", "value": 100.0, "unit": "1/s", "evidence_id": "e3"},
    ])
    r = check_case(case, tolerance_kcal=1.0)
    assert r["status"] == "consistent"
    assert "checks" in r and len(r["checks"]) == 2
    relations = {c["relation"] for c in r["checks"]}
    assert relations == {"dG = RT ln(K)", "Eyring: dG‡ from kcat"}
