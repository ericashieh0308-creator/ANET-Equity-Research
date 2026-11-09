# PR #4 evidence review: bridge, assumptions and FCFF audit

This review advances source verification, **not** a stock recommendation.
Scenario rates were not recalibrated without evidence; Base/Bull/Bear enterprise
values and their WACC/g grids retain their original numbers. New outputs identify
which facts are verified, which transformations are analyst-derived, and which
estimates are still HYPOTHETICAL / NOT YET VALIDATED. Equity/per-share results stay BLOCKED.
Amounts are USD millions unless explicitly stated; ratios in CSVs are fractions.

## Official sources and reproducibility

- [ANET 2025 Form 10-K][K], Item 8 printed pp.68–69 and 72: FY2023–FY2025
  income/cash flows and December 2024/2025 balance sheets. Note 5 p.86: leases.
  Local PDF page = printed page +4. The new `annual_supplement.csv` transcribes
  tax, D&A, SBC and cash-tax fields; `annual_source_extracts.json` preserves
  the relevant existing-PDF excerpts and PDF hash. These fields were also
  checked against the accessible official SEC statements during this review.
- [ANET September 2026 Form 10-Q][Q], filed November 4, 2026, Part I Item 1
  printed pp.1,2,5 and Notes 1–7 pp.6–12. The existing complete official-source
  rendering and CSV reconciliation are reused without alteration.
- Run `python -m anet_research.valuation --output-dir model_outputs` and
  `python -m pytest -q`. Input hashes cover the new evidence. The review
  module reproduces evidence ratios, bridge facts, stub and terminal audits,
  NWC classifications and explicitly labeled CapEx alternatives.

## Bridge: reported amounts do not establish excess cash or dilution

The raw pool is **2,288.1 cash + 12,070.9 securities = 14,359.0** at September 30,
2026 (10-Q p.1). Note 2 pp.7–8 confirms the securities' fair-value presentation.
A **905.2 cash-equivalent investment subset is already within cash**; do not add
it again. **1.5 restricted cash** is in other assets, outside this cash pool;
exclude it without subtracting it again from the p.1 cash balance. Securities
are investments in other issuers' debt, not ANET borrowings. [Q pp.1,7–8][Q]

The code now allocates a single disjoint cash/securities pool. A validated
operating-liquidity reserve consumes cash first, then securities; validated
investment eligibility/tax adjustments reduce the remaining securities. The sum
of additions must equal pool minus reserve minus adjustments. Missing amounts
remain missing, including a reserve or adjustment that might ultimately be zero.
The filings do not quantify an operating cash floor. An investment reserve beyond
the cash balance is permitted, rather than falsely treating all securities as
excess. Restrictions, realization taxes and other required adjustments remain
unvalidated. These are precise economic inputs, not missing balance-sheet totals.

| Claim / denominator | Evidence and treatment |
| --- | --- |
| Funded borrowing | No separate funded debt balance, issuance or repayment is identified in the p.1/p.5 presentation and reviewed notes. The evidence ledger's **zero separately disclosed funded borrowings** is a limited analyst classification, not proof of zero embedded debt-like claims. |
| Other liabilities | **296.4 other current** and **358.1 other long-term liabilities** are reported, but a full operating/tax/debt-like split is not available in the reviewed interim detail. Current operating amounts already deducted in NWC must not be deducted again in the bridge. [Q p.1][Q] |
| Operating leases | 10-K Note 5 p.86 reports **90.5 undiscounted payments at December 2025**, not a September 2026 liability/PV. Do not roll it forward without data. Rent remains in modeled EBIT; no rent add-back or capitalized-lease deduction is applied. A capitalized approach requires coordinated EBIT, FCFF and WACC treatment. [K p.86][K] |
| Preferred / NCI | Preferred shares are nil (Q p.1). Wholly owned subsidiaries and no separate NCI balance support an explicitly **analyst-derived zero NCI component** (Note 1 p.6). These component zeros do not establish zero aggregate other claims. [Q pp.1,6][Q] |
| Operating commitments | **11,400** non-cancellable purchase commitments and **152.8** supplier deposits are disclosed. Do not deduct the entire commitments balance as financial debt while also forecasting the related operating costs/reinvestment. Deposits span current/noncurrent assets, so no invented current allocation is made. [Q Note 4 p.10][Q] |
| Additional nonoperating assets | **899.2 other assets** is an aggregate, not an eligible cash addition. Strategic-investment income is discussed separately; identify any additional nonoperating fair values and overlap rather than assuming the whole balance is excess or silently assuming zero additional assets. This is a separate blocked bridge line. [Q p.1; Item 2 p.17][Q] |
| Point-in-time basic shares | **1,263.4 million** issued/outstanding at September 30, rounded to 0.1 million, is verified. It is not a fully diluted denominator. The later October cover-page count is not substituted. [Q pp.1,4][Q] |
| Awards / EPS shares | **24.3 million unvested RSUs** are reported at September 30. Q3 **1,278.2 million** and 9M **1,276.0 million** diluted shares are period averages using treasury-stock accounting. Do not transplant them into a point-in-time bridge or simply add all RSUs to basic shares. [Q Notes 5–6 pp.11–12][Q] |

The denominator still requires award/ESPP/option terms, vesting and performance
conditions, treatment of remaining services/tax proceeds and an appropriate
as-of-date price or other justified economic valuation method. No price is
invented. The code now refuses `weighted_average_eps` or unresolved share bases
even if someone changes a validation flag. Basic plus gross RSUs is not an
established complete range or a validated treasury-stock share count.

## Historical evidence and scenario assessment

`historical_evidence.csv` contains FY2023–FY2025 and Q3/9M2025–2026 reported
amounts plus separately labeled ratios/proxies. Standalone Q3 cash flow/D&A and
FY2023 NWC stay missing. Annual and interim purchase definitions are not pooled.
`assumption_evidence_matrix.csv` records all 33 scenario-driver choices, historical
comparisons, source locations, judgments and remaining evidence requirements.

Historical ranges provide a **calibration discussion**, not a future confidence
interval or management guidance. Gross margins of roughly 61.95–64.56% and D&A
of 0.75–1.20% of revenue are observed in these periods. The 62.9–64.1% recent
annual/YTD gross-margin window and observed D&A range are reasonable initial
review windows, but not validated long-run assumptions. Bear/Bull gross margins
of 60/65% remain stress hypotheses. [Derived from K pp.69,72; Q pp.2,5][K][Q]

Reported GAAP effective taxes vary roughly **12.65–20.81%**, affected by credits,
equity compensation and deferred taxes; this does not validate a normalized
22% EBIT tax rate. Do not replace it mechanically with the lowest observed rate.
Revenue growth of 19.5%/28.6% in FY2024/FY2025 and 58.5% Q3/44.3% 9M2026
supports studying growth but does not identify Q4 or FY2027–2030 growth. The
10/30/50% Q4 cases and longer-term deceleration remain hypothetical. No dated
risk-free rate, beta, equity risk premium or other WACC components are established
by these filings; 9–12% WACC and 2–3.5% terminal growth remain unvalidated.
[Income inputs K p.69/Q p.2; tax discussion Q Note 7 p.12][K][Q]

## CapEx: classification reconciliation and explicit alternatives

The **combined annual** purchases are 34.4/32.0/119.5 in FY2023/FY2024/FY2025;
**9M PP&E-only** purchases are 82.5/184.9 for 2025/2026. The reviewed cash-flow
statements and asset/commitment notes do not establish a reliable cash-intangible
split. Asset balance changes, amortization, acquisitions and construction
estimates cannot supply that missing cash reconciliation. [K p.72 and Notes 3–5;
Q p.5 and Notes 3–4][K][Q]

Two treatments are now reproduced in `capex_alternatives.csv`:

1. **Extra intangible budget:** the existing PP&E assumptions plus the explicitly
   hypothetical 0.5%-of-revenue cash intangible budget. It is not reported spending.
2. **PP&E-only scope:** omit that extra budget to isolate its valuation effect.
   This is an incomplete total-FCFF scope if intangible investment is needed,
   **not** evidence that actual intangible spending is zero and not a validated upper bound.

Neither treatment splices annual and interim historical FCF. Expensed R&D is
already within EBIT and is not reclassified as cash CapEx without a separate
capitalization/amortization schedule. TTM FCF and TTM EPS remain unavailable.

## Timing, NWC, SBC and terminal audit

**Timing passes:** full FY2026 modeled FCFF minus the elapsed-9M *modeled* FCFF
reconciles exactly to Q4 DCF FCFF in `stub_audit.csv`. Only Q4 is discounted at
0.25 years, then FY2027–FY2030 at 1.25–4.25 years. Normalized operating taxes,
9M intangible budget and economic NWC classification are modeled, not reported
9M FCFF. September 30 is a retrospective reference using the later-filed 10-Q;
this is not an investable contemporaneous backtest.

**NWC remains a material classification gap:** current-only proxy is 267.5 at
December 2025 and 1,051.3 at September 2026 (increase 783.8). Including noncurrent
deferred revenue of 1,369.8/1,737.3 instead gives −1,102.3/−686.0 (increase 416.3).
Both are analyst-derived classifications. Neither equals cash-flow-statement
working-capital effects, which also reflect other operating balances, acquisitions
and noncash adjustments. `nwc_classifications.csv` exposes the difference without
silently changing the forecast's 8–11% target ratios. Any adopted reclassification
requires recalibrating the forecast target and identifying tax/lease/deposit
components, not a one-time cash release. [Q p.1, Note 3 pp.9–10; K p.68][K][Q]

**SBC:** 9M2026 SBC is 379.4, already included in reported costs/expenses. No SBC
add-back or arbitrary repurchase outflow is added to FCFF. That treats future
compensation as an economic operating cost, but does not resolve existing awards.
Before choosing a denominator, separate outstanding award claims from future
compensation/issuance so the same service/award cost is not charged through both
FCFF and dilution. The unresolved denominator prevents a numerical share target.
[Q p.5 and Note 5 p.11][Q]

**Terminal algebra passes; economics need validation:** terminal CapEx − D&A +
change in NWC is now explicit. With stable terminal margins, `g / (reinvestment /
NOPAT)` is an implied *incremental* return, not reported accounting ROIC. The
ratio-budget cases imply persistent high returns, shown below; growth and
reinvestment are therefore not independent free assumptions. A closure such as
FCFF = NOPAT × (1 − g / sustainable incremental return) would require a defensible
return assumption, which is not available. No unsupported terminal benchmark is
inserted merely to force convergence to WACC.

[K]: https://www.sec.gov/Archives/edgar/data/1596532/000159653226000013/anet-20251231.htm
[Q]: https://www.sec.gov/Archives/edgar/data/1596532/000159653226000254/anet-20260930.htm

| Scenario | Terminal reinvestment / NOPAT | Implied incremental return | Status |
| --- | ---: | ---: | --- |
| Base | 6.88% | 43.59% | UNVALIDATED |
| Bull | 6.47% | 54.13% | UNVALIDATED |
| Bear | 9.50% | 21.05% | UNVALIDATED |

## Numerical impact and next review

No operating or discount-rate assumption was changed. Original illustrative EVs
remain Base 86,484.9, Bull 154,717.2 and Bear 38,671.0 (USD millions).
The additional CapEx scope cases are separate audit sensitivities, not a new
recommended valuation range. Equity and per-share results stay BLOCKED.

Ready for another **evidence/model review**, not for a stock-price conclusion.
Priority unresolved decisions are the operating reserve/investment adjustments and additional nonoperating asset fair values,
aggregate claim classification, award-level dilution, calibrated NWC/reinvestment,
normalized operating tax, and sourced WACC/terminal economics.
