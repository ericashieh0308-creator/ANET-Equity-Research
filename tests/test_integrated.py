"""Synthetic valuation controls and reproducible real-evidence schedules."""

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

from anet_research.valuation import (
    ROOT,
    BRIDGE,
    equity_bridge,
    load_inputs,
    forecast,
    ASSUMPTIONS,
)
from anet_research.integrated import (
    dilution_schedule,
    safe_multiple,
    target_and_rating,
    verify_rechecks,
    read,
)


def synthetic_bridge():
    b = json.loads(BRIDGE.read_text())
    b.pop("liquidity_allocation")
    for r in b["inputs"].values():
        r.update(value=1, validated=True, source_reference="Synthetic only")
    b["inputs"]["diluted_shares"]["basis"] = "point_in_time_fully_diluted"
    return b


@pytest.mark.parametrize(
    "field",
    [
        "excess_cash",
        "nonoperating_investments",
        "other_nonoperating_assets",
        "debt_and_debt_like",
        "other_equity_claims",
        "diluted_shares",
    ],
)
@pytest.mark.parametrize("missing", [None, "2025-12-31"])
def test_explicit_bridge_date_required(field, missing):
    b = synthetic_bridge()
    if missing is None:
        b["inputs"][field].pop("reporting_date")
    else:
        b["inputs"][field]["reporting_date"] = missing
    r = equity_bridge(100, b)
    assert r["bridge_status"] == "BLOCKED" and r["equity_value"] is None
    assert "explicit reporting date" in r["bridge_reasons"]


@pytest.mark.parametrize("url", ["", "http://www.sec.gov/a", "https://sec.gov.fake/a"])
def test_bridge_source_url_required(url):
    b = synthetic_bridge()
    b["inputs"]["excess_cash"]["source_url"] = url
    assert equity_bridge(100, b)["equity_value"] is None


@pytest.mark.parametrize(
    "claims",
    [
        {"debt_ids": ["x"], "other_claim_ids": ["x"]},
        {"debt_ids": ["x"], "already_in_operating_nwc": ["x"]},
    ],
)
def test_claim_overlap_and_no_input_mutation(claims):
    b = synthetic_bridge()
    b["claim_classification"] = claims
    before = copy.deepcopy(b)
    assert "double counting" in equity_bridge(100, b)["bridge_reasons"]
    assert b == before


@pytest.mark.parametrize("value", [None, float("nan"), float("inf"), True])
def test_nonfinite_enterprise_value_rejected(value):
    with pytest.raises(ValueError):
        equity_bridge(value, synthetic_bridge())


def dilution_fixture():
    basic = {
        "value": 100,
        "date": "2026-09-30",
        "units": "million shares",
        "validated": True,
        "source_url": "https://www.sec.gov/synthetic",
    }
    award = {
        "id": "synthetic",
        "count": 10,
        "date": "2026-09-30",
        "price_date": "2026-09-30",
        "price": 20,
        "price_units": "USD/share",
        "proceeds_per_award": 5,
        "units": "million shares",
        "validated": True,
        "source_url": "https://www.sec.gov/synthetic",
        "source_reference": "Synthetic award fixture",
        "basis": "point_in_time_treasury_stock",
        "service_cost_policy": "Synthetic costs allocated once",
    }
    return basic, award


def test_dilution_formula_antidilution_and_incomplete_population():
    b, a = dilution_fixture()
    assert dilution_schedule(b, [a], b["date"], True)["diluted_shares"] == 107.5
    a["proceeds_per_award"] = 25
    assert dilution_schedule(b, [a], b["date"], True)["diluted_shares"] == 100
    assert dilution_schedule(b, [a], b["date"])["diluted_shares"] is None
    with pytest.raises(ValueError):
        dilution_schedule(b, [a, a], b["date"], True)


@pytest.mark.parametrize(
    "field,value",
    [
        ("count", None),
        ("price_date", "2026-11-06"),
        ("date", None),
        ("units", "shares"),
        ("basis", "weighted_average_eps"),
        ("service_cost_policy", None),
        ("source_reference", ""),
    ],
)
def test_unsupported_dilution_never_calculated(field, value):
    b, a = dilution_fixture()
    a[field] = value
    assert dilution_schedule(b, [a], b["date"], True)["diluted_shares"] is None


def test_multiple_missing_dates_definitions_and_nonpositive_denominator():
    assert (
        safe_multiple(
            100, 10, "2026-11-06", "2026-09-30", True, "2026-11-04", "2026-09-30"
        )[0]
        == 10
    )
    assert (
        safe_multiple(
            100, 10, "2026-11-06", "2026-09-30", True, "2026-11-07", "2026-09-30"
        )[0]
        is None
    )
    assert (
        safe_multiple(
            100, 10, "2026-11-06", "2026-09-30", True, "2026-11-04", "2026-07-25"
        )[0]
        is None
    )
    for args in [
        (None, 10, "x", "x", True),
        (100, 10, "2026-11-06", "2026-09-30", True),
        (100, 10, "x", "x", False),
        (100, 0, "x", "x", True),
    ]:
        assert safe_multiple(*args)[0] is None


def test_rating_gates_threshold_boundaries_and_no_recommendation_leak():
    gates = {k: True for k in read("rating_policy.json")["requirements"]}
    assert (
        target_and_rating(120, 100, {"buy": 0.1, "sell": -0.1}, gates)["rating"]
        == "Buy"
    )
    assert (
        target_and_rating(80, 100, {"buy": 0.1, "sell": -0.1}, gates)["rating"]
        == "Sell"
    )
    assert (
        target_and_rating(100, 100, {"buy": 0.1, "sell": -0.1}, gates)["rating"]
        == "Hold"
    )
    assert (
        target_and_rating(100, 100, {"buy": 0, "sell": -0.1}, gates)["rating"] == "Hold"
    )
    for key in gates:
        missing = {**gates, key: False}
        r = target_and_rating(120, 100, {"buy": 0.1, "sell": -0.1}, missing)
        assert (
            r["rating"] == "NOT RATED"
            and r["target"] is None
            and r["upside_downside"] is None
        )
    assert (
        target_and_rating(120, 100, {"buy": None, "sell": None}, gates)["rating"]
        == "NOT RATED"
    )
    with pytest.raises(ValueError):
        target_and_rating(120, 0, {"buy": 0.1, "sell": -0.1}, gates)


def test_real_schedules_sources_scope_and_blockers():
    rechecks = verify_rechecks()
    assert len(rechecks) == 32 and rechecks.difference.eq(0).all()
    p = pd.read_csv(ROOT / "model_outputs/integrated/peer_comparison.csv")
    assert p.ticker.tolist() == ["ANET", "CSCO", "NVDA"] and p.period_end.nunique() == 3
    assert p[["ev_revenue", "ev_ebitda", "forward_pe"]].isna().all().all()
    for r in p.itertuples():
        assert r.revenue_growth == pytest.approx(r.revenue / r.prior_revenue - 1)
        assert r.operating_margin == pytest.approx(r.operating_income / r.revenue)
        assert r.source_url.startswith("https://www.sec.gov/")
    ready = json.loads(
        (ROOT / "model_outputs/integrated/valuation_readiness.json").read_text()
    )
    assert ready["dilution"]["diluted_shares"] is None
    assert (
        ready["target_rating"]["target"] is None
        and ready["target_rating"]["rating"] == "NOT RATED"
    )
    assert ready["price_reference"]["value"] == 170.8
    f = pd.read_csv(ROOT / "model_outputs/integrated/financial_analysis.csv").set_index(
        "period"
    )
    assert pd.isna(f.loc["Q3 2026", "operating_cash_flow"])
    assert f.loc["9M 2026", "operating_cash_flow"] == 3977.4


def test_sbc_not_added_to_fcff_and_original_evs_retained():
    cfg = json.loads(ASSUMPTIONS.read_text())
    for name, s in cfg["scenarios"].items():
        f = forecast(load_inputs(), s, name)
        assert (
            f.annual_fcff - (f.nopat + f.da - f.total_modeled_capex - f.change_nwc)
        ).abs().max() < 1e-8
    ev = pd.read_csv(ROOT / "model_outputs/scenario_dcf.csv").set_index("scenario")
    for name, value in [
        ("Base", 86484.888644),
        ("Bull", 154717.241798),
        ("Bear", 38671.019917),
    ]:
        assert ev.loc[name, "enterprise_value"] == pytest.approx(value)
        assert ev.loc[name, "bridge_status"] == "BLOCKED"


def test_integrated_manifest_and_schedule_reproduction():
    folder = ROOT / "model_outputs/integrated"
    manifest = json.loads((folder / "manifest.json").read_text())
    for group in ["input_sha256", "output_sha256"]:
        for path, digest in manifest[group].items():
            assert (
                hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
            ), path
    before = {p.name: p.read_bytes() for p in folder.iterdir()}
    subprocess.run(
        [sys.executable, "-m", "anet_research.integrated"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert before == {p.name: p.read_bytes() for p in folder.iterdir()}


@pytest.mark.parametrize(
    "field,value",
    [("value", None), ("date", None), ("units", "shares"), ("validated", False)],
)
def test_missing_basic_share_evidence_blocks(field, value):
    b, a = dilution_fixture()
    b[field] = value
    assert dilution_schedule(b, [a], "2026-09-30", True)["diluted_shares"] is None


def test_missing_all_bridge_inputs_and_invalid_dilution_date():
    b = json.loads(BRIDGE.read_text())
    b.pop("inputs")
    assert equity_bridge(100, b)["equity_value"] is None
    basic, a = dilution_fixture()
    with pytest.raises(ValueError):
        dilution_schedule(basic, [a], "not-a-date", True)
