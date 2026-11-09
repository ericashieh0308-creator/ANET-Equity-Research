# Integrated valuation, source review and investment framework

Research date: November 8, 2026 (America/New_York). Baseline main: `6c1498f`.
This is an evidence-controlled portfolio model, not a validated investment recommendation.

## Evidence and financial analysis

[Source review register](../data/integrated/source_review.json) records a fresh direct
inspection of official ANET SEC HTML: 24 annual statement figures (FY2023–2025
revenue, cost of revenue, gross profit, OpEx, EBIT, net income, OCF and combined
purchase outflows) and eight interim revenue/net-income figures across Q3/9M2025–26.
All 32 agree with preserved historical CSVs. No historical number was rewritten.
This is a scoped source recheck, not an independent audit or re-verification of
all 190 previously reconciled interim values. Existing strict loaders separately
reconcile saved filing snapshots, statement arithmetic and historical fingerprints.

- [2025 10-K](https://www.sec.gov/Archives/edgar/data/1596532/000159653226000013/anet-20251231.htm): Item 8 pp.68–69,72; existing annual PDF page = printed page +4.
- [Q3 2026 10-Q](https://www.sec.gov/Archives/edgar/data/1596532/000159653226000254/anet-20260930.htm): Part I Item 1 pp.1,2,5; Notes 2–7 pp.7–12; Item 2 pp.14–19.
- [Filing index](https://www.sec.gov/Archives/edgar/data/1596532/000159653226000254/0001596532-26-000254-index.html): period September 30, 2026; filing date November 4; acceptance November 3 at 18:50:52. Acceptance and filing dates are distinct.

`model_outputs/integrated/financial_analysis.csv` separates reported figures from
ratios. Revenue growth uses matched durations; margins and OpEx/revenue measure
observed operating leverage, not permanent scale benefits. OCF/EBIT is only a
cash-conversion diagnostic: OCF includes taxes, investment-income cash effects
and SBC adjustments and is not FCFF. Q3 cash flow stays absent. TTM diluted EPS
and TTM FCF remain unavailable. FY2023 balance-sheet coverage remains incomplete.

## Bridge classification and residual blockers

[Ledger](../model_outputs/integrated/bridge_classification_ledger.csv) preserves
reported component values, dates, source locations, classification decisions and
null eligible adjustments. A reported amount is not automatically a bridge input.
See also [the existing evidence review](valuation_evidence_review.md).

Equity = operating EV + excess cash + eligible investments + eligible other
nonoperating assets − funded/debt-like claims − other equity claims. Bridge
amounts are USD millions; valuation shares are million shares, yielding USD/share.

The liquidity pool is 2,288.1 cash + 12,070.9 securities; the 905.2 investment
subset inside cash is never added again. Restricted cash 1.5 sits outside that
pool. Operating liquidity reserve and any investment eligibility/realization
adjustments remain unknown, not zero. No generic cash/revenue haircut is invented.
The official Q Note 2 p.8 describes securities as available to support operations;
that does not quantify how much is excess. [Q pp.1,7–8]

Other current liabilities 296.4 are already in the current NWC proxy. Other
long-term liabilities 358.1 and aggregate other assets 899.2 require economic
classification. A balance-sheet debt line's absence is not proof of zero embedded
claims. Preferred and derived NCI zero components do not establish a zero aggregate.
Operating commitments are not automatically debt; forecasts already include
related operating costs. Lease rent remains in EBIT without capitalization.
A new claim-ID overlap check blocks deductions already allocated to NWC or
another claims line. Identification of an omitted component cannot be solved by
changing a validation flag. [Q pp.1,6,10; K Note 5 p.86]

Code now requires **explicit** same-date input dates, official HTTPS SEC source
URLs, finite values, proper units and a point-in-time fully diluted basis. The
old missing-date default has been removed. These are validation controls, not
proof of economic judgments: reviewers must still substantiate each classification.

## Diluted equity schedule and SBC policy

[Schedule](../model_outputs/integrated/diluted_share_schedule.csv) starts with
September basic shares of 1,263.4m and identifies 24.3m unvested RSUs. The
point-in-time historical price of 203.59 is sourced separately; price availability
alone does not establish award proceeds, remaining service cost, forfeiture,
vesting or performance conditions, or complete option/ESPP coverage. Grant-date
fair value is not an exercise price or a treasury-stock proceeds input. The
reported $1.7bn remaining compensation cost is not automatically a cash strike.
Q3/9M weighted-average diluted EPS shares are excluded. [Q Notes 5–6 pp.11–12]

`dilution_schedule()` implements award-level incremental shares = award count ×
max(0, 1 − justified proceeds per award / same-date price). It requires complete
population evidence, terms, prices, units, explicit source locations and an
SBC service-cost policy. The real schedule remains BLOCKED. Synthetic tests
exercise eligible, antidilutive, missing, mismatched-date and duplicate cases.
Future SBC stays in EBIT, with no SBC add-back or arbitrary repurchase deduction.
Existing vested/unvested claims must be distinguished from future compensation
so the same service cost is not charged in both FCFF and dilution.

## Assumptions, reinvestment and WACC

[Matrix](../model_outputs/integrated/assumption_evidence_matrix.csv) retains all
33 prior scenario-driver rows, evidence and open questions. **All forward rates
remain HYPOTHETICAL / NOT YET VALIDATED.** No growth, tax, margin, reinvestment,
WACC or terminal-growth choice was newly validated or changed.

Historical margin/DA/GAAP tax ranges are calibration context, not guidance.
A defensible forecast requires product/service demand, customer timing, cost mix,
normalized operating taxes, asset spending and economically classified NWC.
WACC still lacks a dated risk-free-rate/beta/ERP/financing-cost/weight package;
no market benchmark is invented. Terminal growth requires a mature reinvestment
and incremental-return argument, not simply a number below WACC.

Annual purchases include property/equipment/intangibles; interim purchases are
PP&E only. Existing extra-intangible-budget and PP&E-only alternatives remain
separate scope illustrations, not an invented numerical split. NWC alternatives
require recalibrated target ratios. Terminal reinvestment diagnostics imply high,
unvalidated incremental returns; terminal value accounts for about 69–84% of
scenario EV. Do not mechanically extrapolate these returns.

The September 30 DCF uses information filed later on November 4. Only Q4 FY2026
is discounted at 0.25 years, then FY2027–2030 at 1.25–4.25. Annual minus modeled
9M FCFF reconciles to the stub; modeled normalized taxes and NWC are not reported
actual FCFF. Scenario EVs and all original forecast/sensitivity figures remain
unchanged because no legitimate recalibration evidence was established.

## Peer valuation discipline

[Peer analysis and limitations](peer_valuation.md) and its CSV provide sourced
consolidated operating context for ANET, Cisco and NVIDIA. Fiscal dates are
explicit, not silently aligned. Trading multiples and the quantitative DCF peer
cross-check remain BLOCKED pending common-date market caps, balance-sheet bridges,
calendarized TTM revenue/EBITDA and reliable dated NTM EPS. An illustrative ANET
DCF EV must never stand in for market EV in a trading-comparables table.

## Reproduction and outputs

```bash
python -m anet_research.valuation --output-dir model_outputs
python -m anet_research.integrated
python scripts/build_integrated_report.py
python -m pytest -q
```

Install `requirements-report.txt` for PDF validation. Builds are offline, write
only dedicated model/report artifacts and never alter original workbooks or
historical financial CSVs. Each layer records hashes. The previous eight-page
PDF, editable source and builder remain unchanged; a byte-identical PDF copy
is also retained under `reports/archive/`. See [price target and rating policy](price_target_framework.md)
and [balanced thesis/catalysts](investment_framework.md). BLOCKED means an
unsupported output, not a hidden zero or an assigned Hold recommendation.
