"""Evidence schedules and gated valuation frameworks; no network or dashboard writes."""

from datetime import date
import hashlib
import json
from pathlib import Path

import pandas as pd

from .valuation import ROOT, BRIDGE, ASSUMPTIONS, finite, load_inputs
from .valuation_review import historical_evidence, reviewed_bridge_evidence

DATA = ROOT / "data/integrated"
OUT = ROOT / "model_outputs/integrated"


def read(name):
    return json.loads((DATA / name).read_text())


def dilution_schedule(basic, awards, reference_date, population_complete=False):
    """Award-level economic dilution schedule. Caller must justify service-cost policy.

    TSM incremental = count * max(0,1-proceeds_per_award/dated_price).
    Gross vested/unissued shares can use count only where no service/vesting claim
    remains. No EPS averages, gross unvested RSU sums or arbitrary haircut accepted.
    """
    date.fromisoformat(reference_date)
    reasons = []
    rows = []
    if (
        basic.get("date") != reference_date
        or basic.get("units") != "million shares"
        or basic.get("validated") is not True
        or not basic.get("source_url")
        or basic.get("value") is None
    ):
        reasons.append("Missing dated, sourced basic share count.")
    base = None if reasons else finite(basic.get("value"), "basic shares")
    if base is not None and base <= 0:
        raise ValueError("Basic shares must be positive.")
    if not population_complete:
        reasons.append("Award/option/ESPP population completeness not established.")
    seen = set()
    for award in awards:
        if not award.get("id") or award["id"] in seen:
            raise ValueError("Award IDs must be present and unique.")
        seen.add(award["id"])
        increment = None
        reason = ""
        needed = [
            "count",
            "proceeds_per_award",
            "price",
            "source_url",
            "source_reference",
            "service_cost_policy",
        ]
        if (
            award.get("date") != reference_date
            or award.get("price_date") != reference_date
            or award.get("validated") is not True
            or any(award.get(k) is None or award.get(k) == "" for k in needed)
        ):
            reason = "Missing same-date award terms, price, vesting/proceeds or SBC service-cost policy."
        elif (
            award.get("units") != "million shares"
            or award.get("price_units") != "USD/share"
            or award.get("basis") != "point_in_time_treasury_stock"
        ):
            reason = "Incompatible share/price units or non-point-in-time award basis."
        else:
            count = finite(award["count"], "award count")
            proceeds = finite(award["proceeds_per_award"], "proceeds")
            price = finite(award["price"], "award price")
            if count < 0 or proceeds < 0 or price <= 0:
                raise ValueError("Invalid award quantities/proceeds/price.")
            increment = count * max(0, 1 - proceeds / price)
        if reason:
            reasons.append(award["id"] + ": " + reason)
        rows.append(
            dict(
                id=award["id"],
                count=award.get("count"),
                incremental_shares=increment,
                status="BLOCKED" if reason else "ANALYST_DERIVED",
                reason=reason,
            )
        )
    return {
        "status": (
            "BLOCKED" if reasons else "ANALYST_DERIVED; requires economic policy review"
        ),
        "basic_shares": base,
        "diluted_shares": (
            None if reasons else base + sum(r["incremental_shares"] for r in rows)
        ),
        "reasons": reasons,
        "awards": rows,
    }


def safe_multiple(
    numerator,
    denominator,
    numerator_date,
    denominator_end,
    definition_verified=False,
    financial_available_date=None,
    comparison_period_end=None,
):
    """Common-date market EV / common-period TTM, published by valuation date.

    A November quote may properly use September TTM data filed in early November;
    market and financial period end need not be identical. Comparisons require an
    explicit common TTM end and publication date, never invented calendarization.
    """
    if numerator is None or denominator is None:
        return None, "BLOCKED: missing verified numerator or denominator"
    try:
        market = date.fromisoformat(numerator_date)
        period = date.fromisoformat(denominator_end)
        available = date.fromisoformat(financial_available_date)
        common = date.fromisoformat(comparison_period_end)
    except (TypeError, ValueError):
        return (
            None,
            "BLOCKED: explicit ISO market, period, publication and comparison dates required",
        )
    if not definition_verified:
        return None, "BLOCKED: financial definition not verified"
    if period != common or not period <= available <= market:
        return (
            None,
            "BLOCKED: inconsistent common TTM period or information unavailable at valuation date",
        )
    n, d = finite(numerator, "multiple numerator"), finite(
        denominator, "multiple denominator"
    )
    if n < 0 or d <= 0:
        return None, "NM: nonpositive denominator or negative numerator"
    return n / d, "ANALYST_DERIVED"


def target_and_rating(target, price, thresholds, gates):
    """No numeric target can escape missing evidence gates; thresholds are policy inputs."""
    required = read("rating_policy.json")["requirements"]
    missing = [k for k in required if gates.get(k) is not True]
    low, high = thresholds.get("sell"), thresholds.get("buy")
    if target is None or price is None:
        missing.append("supported 12-month target and reference price")
    if low is None or high is None:
        missing.append("explicit analyst rating policy thresholds")
    if missing:
        return dict(
            status="BLOCKED",
            target=None,
            upside_downside=None,
            rating="NOT RATED",
            reasons=missing,
        )
    p, t = finite(price, "reference price"), finite(target, "12-month target")
    low, high = finite(low, "sell threshold"), finite(high, "buy threshold")
    if p <= 0 or t <= 0 or low >= high:
        raise ValueError(
            "Require positive prices and sell threshold below buy threshold."
        )
    ret = t / p - 1
    return dict(
        status="FRAMEWORK CALCULATION; not an automatic recommendation",
        target=t,
        upside_downside=ret,
        rating="Buy" if ret > high else "Sell" if ret < low else "Hold",
        reasons=[],
    )


def verify_rechecks():
    review = read("source_review.json")
    annual = pd.read_csv(ROOT / "data/verified_2023_2025.csv").set_index("fiscal_year")
    interim = pd.read_csv(ROOT / "data/quarterly/anet_20260930_metrics.csv").set_index(
        "period"
    )
    rows = []
    for table, key in [(annual, "annual_rechecks"), (interim, "interim_rechecks")]:
        for row in review[key]:
            period = (
                int(row["period"][2:]) if key == "annual_rechecks" else row["period"]
            )
            value = float(table.loc[period, row["metric"]])
            difference = value - row["value"]
            if abs(difference) > 1e-8:
                raise ValueError("SEC recheck mismatch: " + str(row))
            rows.append(
                dict(**row, repository_value=value, difference=difference, check="PASS")
            )
    return pd.DataFrame(rows)


def build():
    # Existing strict loaders perform local historical, filing-snapshot and arithmetic checks.
    load_inputs()
    facts = reviewed_bridge_evidence()
    bridge = json.loads(BRIDGE.read_text())
    rows = []
    treatment = {
        "cash_and_equivalents": (
            "Potential addition",
            "Operating reserve unresolved; cash-equivalent subset already included.",
        ),
        "marketable_securities": (
            "Potential addition",
            "Use remaining disjoint pool after reserve and eligibility/tax adjustments.",
        ),
        "cash_equivalent_investments_subset": (
            "Excluded duplicate",
            "Already within cash; never add again.",
        ),
        "restricted_cash": (
            "Excluded",
            "Outside unrestricted pool; do not subtract it twice.",
        ),
        "other_current_liabilities": (
            "Classification blocked",
            "Currently in NWC proxy; no bridge deduction without reclassification.",
        ),
        "other_long_term_liabilities": (
            "Classification blocked",
            "Operating/tax/lease/financial components unresolved.",
        ),
        "other_assets": (
            "Potential addition blocked",
            "Aggregate not eligible fair value; identify holdings and securities overlap.",
        ),
        "historical_operating_lease_payments": (
            "Operating policy",
            "2025 undiscounted payments are not 2026 debt; rent remains EBIT expense.",
        ),
        "purchase_commitments": (
            "Operating exposure",
            "Not automatically financial debt; avoid deducting procurement and forecasting costs twice.",
        ),
    }
    for r in facts.to_dict("records"):
        action, reason = treatment.get(
            r["id"],
            (
                "Evidence only",
                "Not an automatically eligible bridge adjustment; see source scope.",
            ),
        )
        rows.append(
            dict(
                **r,
                bridge_action=action,
                decision_reason=reason,
                eligible_bridge_adjustment=None,
            )
        )
    for key, r in bridge["inputs"].items():
        rows.append(
            dict(
                id="aggregate_" + key,
                value=r["value"],
                units=r["units"],
                reporting_date=r["reporting_date"],
                source_url=r["source_url"],
                source_reference=r["source_reference"],
                classification="UNRESOLVED",
                bridge_action="BLOCKED",
                decision_reason=r["reason"],
                eligible_bridge_adjustment=None,
            )
        )
    ledger = pd.DataFrame(rows)
    basic = {
        "value": 1263.4,
        "date": "2026-09-30",
        "units": "million shares",
        "validated": True,
        "source_url": facts.loc[
            facts.id.eq("basic_shares_point_in_time"), "source_url"
        ].iloc[0],
    }
    award = {
        "id": "unvested_RSU_population",
        "count": 24.3,
        "date": "2026-09-30",
        "price_date": "2026-09-30",
        "price": 203.59,
        "price_units": "USD/share",
        "units": "million shares",
        "basis": "point_in_time_treasury_stock",
        "proceeds_per_award": None,
        "validated": False,
        "source_url": basic["source_url"],
        "source_reference": "10-Q Note 5 p.11",
        "service_cost_policy": None,
    }
    dilution = dilution_schedule(basic, [award], "2026-09-30")
    shares = [
        dict(
            component="Point-in-time basic",
            value=1263.4,
            units="million shares",
            date="2026-09-30",
            status="REPORTED",
            formula="Starting issued/outstanding balance, rounded",
            source_url=basic["source_url"],
            source_reference="10-Q pp.1,4",
        )
    ]
    for r in dilution["awards"]:
        shares.append(
            dict(
                component=r["id"],
                value=r["count"],
                incremental_shares=r["incremental_shares"],
                units="million shares",
                date="2026-09-30",
                status=r["status"],
                formula="count × max(0, 1 − justified proceeds per award / same-date price)",
                reason=r["reason"],
                source_url=basic["source_url"],
                source_reference="10-Q Notes 5–6 pp.11–12",
            )
        )
    shares.append(
        dict(
            component="Fully diluted valuation denominator",
            value=dilution["diluted_shares"],
            units="million shares",
            date="2026-09-30",
            status="BLOCKED",
            reason="; ".join(dilution["reasons"]),
            formula="basic + eligible incremental awards; EPS averages excluded",
        )
    )
    peers = []
    for r in read("peer_inputs.json"):
        for field in ["revenue", "prior_revenue", "operating_income"]:
            if f"{r[field]:,.0f}" not in r["source_excerpt"]:
                raise ValueError(
                    "Peer transcription mismatch: " + r["ticker"] + " / " + field
                )
        peers.append(
            dict(
                **r,
                revenue_growth=r["revenue"] / r["prior_revenue"] - 1,
                operating_margin=r["operating_income"] / r["revenue"],
                ev_revenue=None,
                ev_ebitda=None,
                forward_pe=None,
                valuation_date="2026-11-06",
                status="Historical operating context only; trading comparison BLOCKED",
                reason="No verified common-date peer market capitalization/EV bridges or calendarized TTM; pure D&A and dated forward EPS missing. Fiscal periods differ; do not rank consolidated margins or infer fair ANET multiples.",
            )
        )
    annual = pd.read_csv(ROOT / "data/verified_2023_2025.csv").set_index("fiscal_year")
    r = annual.loc[2025]
    peers.insert(
        0,
        dict(
            ticker="ANET",
            company="Arista Networks",
            fiscal_year="FY2025",
            period_start="2025-01-01",
            period_end="2025-12-31",
            prior_period_end="2024-12-31",
            revenue=r.revenue,
            prior_revenue=annual.loc[2024, "revenue"],
            operating_income=r.operating_income,
            revenue_growth=r.revenue / annual.loc[2024, "revenue"] - 1,
            operating_margin=r.operating_income / r.revenue,
            units="USD millions",
            source_url=r.source_url,
            source_reference="10-K Item 8 p.69",
            comparability="Subject company; periods not calendarized against peers",
            ev_revenue=None,
            ev_ebitda=None,
            forward_pe=None,
            valuation_date="2026-11-06",
            status="Historical context only; trading comparison BLOCKED",
            reason="No dated common-date market-cap share schedule/equity bridge or validated NTM EPS. Illustrative DCF EV is not a market trading EV.",
        ),
    )
    a = historical_evidence()
    a["operating_leverage_note"] = (
        "Compare matched durations only; lower OpEx ratio is derived, not evidence of permanent scale economics."
    )
    statements = pd.read_csv(
        ROOT / "data/quarterly/anet_20260930_metrics.csv"
    ).set_index("period")
    a["operating_cash_flow"] = [
        (
            float(statements.loc[p, "operating_cash_flow"])
            if p in statements.index
            else float(
                pd.read_csv(ROOT / "data/verified_2023_2025.csv")
                .set_index("fiscal_year")
                .loc[int(p[2:]), "operating_cash_flow"]
            )
        )
        for p in a.period
    ]
    a["ocf_to_operating_income"] = a.operating_cash_flow / a.operating_income
    a["cash_conversion_note"] = (
        "Reported OCF includes nonoperating tax/interest and SBC effects; this ratio is not unlevered FCFF conversion."
    )
    market = read("market_reference.json")
    for observation in market["observations"]:
        if date.fromisoformat(observation["date"]) > date.fromisoformat(
            read("rating_policy.json")["research_date"]
        ):
            raise ValueError("Future price observation.")
        if len(observation["sources"]) < 2 or observation["value"] <= 0:
            raise ValueError("Uncorroborated price.")
        for src in observation["sources"]:
            if (
                f"{observation['value']:.2f}" not in src["excerpt"]
                or observation["date"] not in src["excerpt"]
            ):
                raise ValueError("Quote source mismatch.")
    rating = target_and_rating(
        None,
        market["observations"][-1]["value"],
        {"buy": None, "sell": None},
        {"verified_reference_price": True},
    )
    files = {
        "bridge_classification_ledger.csv": ledger,
        "diluted_share_schedule.csv": pd.DataFrame(shares),
        "peer_comparison.csv": pd.DataFrame(peers),
        "financial_analysis.csv": a,
        "sec_rechecks.csv": verify_rechecks(),
        "assumption_evidence_matrix.csv": pd.read_csv(
            ROOT / "model_outputs/assumption_evidence_matrix.csv"
        ).assign(
            upgrade_review="Future rate remains HYPOTHETICAL / NOT YET VALIDATED; no evidence-based recalibration in this pass"
        ),
    }
    OUT.mkdir(exist_ok=True)
    for name, frame in files.items():
        frame.to_csv(OUT / name, index=False, float_format="%.10g")
    (OUT / "valuation_readiness.json").write_text(
        json.dumps(
            {
                "equity_bridge_status": "BLOCKED",
                "dilution": dilution,
                "target_rating": rating,
                "price_reference": market["observations"][-1],
                "scenario_policy": "Original EVs unchanged; no new operating/discount assumptions introduced.",
                "blocker_summary": {
                    "equity_bridge": "Operating liquidity reserve/investment adjustments, 899.2 other assets eligibility and aggregate 296.4/358.1 liability classifications unresolved.",
                    "diluted_shares": "Complete options/ESPP/award population, vesting/performance terms, proceeds and remaining-service/SBC economic policy unresolved; EPS averages excluded.",
                    "operating_assumptions": "Growth, margins, normalized operating taxes, D&A, intangible investment and economic NWC/target ratios remain hypothetical.",
                    "discount_terminal": "No validated dated WACC component package or sustainable terminal reinvestment/return rationale.",
                    "twelve_month_target": "No supported horizon-specific revaluation or future cash/claims/share schedule; rating thresholds unset.",
                    "peer_cross_check": "No verified common-date peer market EVs, calendarized TTM EBITDA/revenue or dated NTM EPS.",
                },
            },
            indent=2,
        )
        + "\n"
    )
    paths = sorted(
        list(DATA.glob("*.json"))
        + [
            BRIDGE,
            ASSUMPTIONS,
            ROOT / "anet_research/integrated.py",
            ROOT / "anet_research/valuation.py",
            ROOT / "anet_research/valuation_review.py",
            ROOT / "model_outputs/manifest.json",
            ROOT / "model_outputs/assumption_evidence_matrix.csv",
            ROOT / "data/verified_2023_2025.csv",
            ROOT / "data/valuation/bridge_evidence.json",
            ROOT / "data/valuation/annual_supplement.csv",
            ROOT / "data/valuation/annual_source_extracts.json",
        ]
        + list((ROOT / "data/quarterly").glob("*"))
    )
    (OUT / "manifest.json").write_text(
        json.dumps(
            {
                "input_sha256": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in paths
                },
                "output_sha256": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(OUT.iterdir())
                    if p.name != "manifest.json"
                },
            },
            indent=2,
        )
        + "\n"
    )
    print(
        "Integrated schedules written; equity value, per-share, 12-month target and rating remain BLOCKED."
    )


if __name__ == "__main__":
    build()
