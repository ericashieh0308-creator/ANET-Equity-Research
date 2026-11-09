# ANET FY2026–FY2030 forecast and FCFF DCF — illustrative v1

**Every scenario and valuation output is HYPOTHETICAL / NOT YET VALIDATED.**
Base, Bull and Bear are demonstration cases, not management guidance, probabilities,
a forecast endorsement, target prices or investment recommendations. No current
stock price is supplied. Existing historical data and dashboard files are unchanged.

## Reproduce

From the repository root, using the existing Python dependencies:

```bash
python -m anet_research.valuation --output-dir model_outputs
python -m pytest -q
```

The first command only writes the dedicated `model_outputs/` directory. It rejects
other output directories and output-file symlinks. Input JSON files live under
`data/valuation/`; no secrets, API keys or new network downloads are needed.
`manifest.json` records input SHA-256 hashes and official filing references.
Changing hypotheses and rerunning refreshes all tables; tests detect stale outputs.

## Historical inputs versus assumptions

The loader reuses the existing annual fingerprint verification, interim source
snapshot hashes, 190-value reconciliation and statement arithmetic checks.
The [2025 ANET 10-K](https://www.sec.gov/Archives/edgar/data/1596532/000159653226000013/anet-20251231.htm),
Item 8 printed p.69 (local PDF p.73), supplies FY2025 income. The
[September 2026 ANET 10-Q](https://www.sec.gov/Archives/edgar/data/1596532/000159653226000254/anet-20260930.htm),
Part I Item 1, printed pp.1, 2 and 5 supplies dated balance sheets, income and
nine-month cash flows. FY2025 and 9M2025 revenue imply Q4 2025 revenue of
2,487.8; this is a subtraction of verified figures, not separately reported Q4 data.
The retained 9M2026 inputs are revenue 9,402.3, gross profit 5,912.8, OpEx 1,734.6,
D&A 70.3 and cash PP&E purchases of 184.9 (outflow magnitude). Amounts are USD millions.
See `historical_inputs.csv` for value-level source, period and verification status.

### NWC proxy, not a validated economic classification

Opening December 2025 and September 2026 balances come from 10-Q p.1.
Proxy NWC = receivables + inventories + prepaid/other current assets − accounts
payable − accrued liabilities − current deferred revenue − other current liabilities.
It excludes cash, marketable securities and noncurrent balances. The resulting
267.5 and 1,051.3 are **derived proxies**, not reported operating-NWC line items.
The difference is not a substitute for the statement's operating cash flow.
Supplier deposits, deferred cost of sales, tax-related balances, financing items
and deferred-revenue economics need line-by-line classification. The unchanged
proxy is used throughout this illustration; its suitability is unvalidated.

## Explicit scenario assumptions

All percentages below are fractions in the input/output CSVs. Each is
**HYPOTHETICAL / NOT YET VALIDATED**, including the reinvestment and tax settings.
The cases vary economics and discount rates together; the sensitivity table
separately varies only WACC and terminal growth while holding each case fixed.

| Driver | Base | Bull | Bear |
| --- | ---: | ---: | ---: |
| Q4 2026 revenue YoY | 30% | 50% | 10% |
| FY2027–FY2030 annual growth | 20%, 16%, 12%, 10% | 28%, 24%, 20%, 16% | 10%, 8%, 6%, 4% |
| Q4 2026 and subsequent annual gross margin | 63% | 65% | 60% |
| OpEx / revenue, same forecast periods | 19% | 18% | 22% |
| Normalized operating tax rate | 22% | 22% | 22% |
| Future D&A / revenue | 0.9% | 0.9% | 0.9% |
| Future PP&E cash investment / revenue | 2.5% | 2.5% | 3.0% |
| Additional modeled intangible cash investment / revenue | 0.5% | 0.5% | 0.5% |
| Year-end NWC proxy / annual revenue | 9% | 8% | 11% |
| WACC | 10% | 9% | 12% |
| Perpetual terminal growth | 3% | 3.5% | 2% |

These values exercise the model and are not empirically calibrated. Required evidence:

- **Revenue:** validate customer budgets, acceptance timing, product/service mix,
  seasonality and competitive wins. Use the 10-Q Item 2 demand discussion
  (pp.14–16) as a starting point, not as support for these particular growth rates.
- **Margins/OpEx:** validate mix, pricing, silicon costs, R&D and selling costs
  against annual p.69/interim p.2 and management's margin discussion (10-Q p.16).
  FY2026 full-year margins are blended actual/model ratios, not the Q4 assumptions.
- **Taxes:** validate normalized marginal operating taxes, geographic mix, tax credits
  and cash/deferred effects using 10-Q Note 7 (p.12) and 10-K Note 8 (pp.90–93).
  Reported corporate effective tax rates are not automatically NOPAT tax rates.
- **D&A:** validate asset lives, depreciation, acquisition amortization and future
  investment against 10-Q p.5 and Note 3 (p.9). The forecast ratio is unsupported.
- **CapEx:** validate maintenance/growth PP&E, construction and cash intangible
  purchases separately; acquisitions are not ordinary CapEx in this model.
- **NWC:** validate proxy composition and seasonal target ratios using detailed
  balances and notes, including deferred revenue and deposits; revenue ratios
  alone do not establish working-capital requirements.
- **WACC/terminal growth:** source a dated risk-free rate, equity risk premium,
  beta, borrowing cost and financing weights. Validate mature growth, returns
  and reinvestment rather than treating the demonstration rates as market facts.
- **Cash/debt/shares:** validate a same-date, nonoverlapping enterprise-to-equity
  bridge and a fully diluted share denominator, as described below. Start with the 10-Q
  balance sheet (p.1) and Note 6 share/EPS reconciliation (pp.11–12), then
  validate debt-like claims, leases and dilution against the relevant notes;
  do not substitute cover-page basic shares or quarterly EPS denominators.

## FY2026 partial-year treatment and FCFF

FY2026 revenue = reported 9M2026 revenue + derived Q4 2025 revenue ×
(1 + hypothetical Q4 revenue growth). Gross profit and operating expenses retain
their 9M reported amounts and add Q4 revenue × forecast gross margin/OpEx ratios.
FY2027–FY2030 are fully modeled annual estimates.

For each year:

- EBIT = gross profit − operating expenses; operating margin = EBIT / revenue.
- Modeled operating taxes = EBIT × assumed normalized tax rate.
- NOPAT = EBIT × (1 − tax rate).
- FCFF = NOPAT + D&A − total modeled CapEx − change in proxy NWC.

Loss tax shields are assumed immediately usable, an unvalidated simplification;
none of the supplied cases has a loss. Stock compensation remains in operating
expenses and is not added back separately. This does not resolve share dilution.
D&A is the reported cash-flow add-back plus modeled Q4 D&A in FY2026; later
periods use the assumed ratio. Taxes on historical EBIT are modeled operating
taxes, not reported tax expense. Negative change in NWC produces a release;
no release is silently capped or described as reported cash flow.

### CapEx definition reconciliation: scope known, numerical split unresolved

The annual cash-flow line is **purchases of property, equipment and intangible
assets** (10-K p.72). The interim line is **purchases of property and equipment**
(10-Q p.5). The combined FY2025 amount of 119.5 cannot establish FY2025 PP&E-only
spending. Its difference from a nine-month figure also mixes incompatible periods.
No annual PP&E/intangible cash split has been validated; zero intangible spending
must not be inferred from the interim label.

The model therefore uses a **separate hypothetical total reinvestment budget**:
reported 9M2026 PP&E outflow + modeled Q4 PP&E + hypothetical intangible
reinvestment on full-year revenue. The extra 0.5% allocation is not a disclosed
intangible purchase amount, including its elapsed-9M portion. That unresolved
scope is a limitation of modeled FCFF, not a historical fact. FY2027 onward uses
PP&E and intangible budget ratios separately. Historical annual FCF and interim
PP&E-only FCF are never concatenated. No TTM FCF or TTM EPS is produced.

## DCF timing and terminal value

**Reference date: September 30, 2026.** The 10-Q was filed November 4, 2026.
This is a retrospective analytical reference date, not an implementable
September 30 trading recommendation or backtest using then-available information.
The supplied WACC is an annual effective rate; end-of-period discounting is used.

- FY2026 DCF cash flow includes **only modeled Q4 FCFF**: Q4 NOPAT + Q4 modeled
  D&A − Q4 modeled PP&E/intangibles − (modeled December NWC − September proxy NWC).
- The full FY2026 annual FCFF includes elapsed-9M model components for completeness,
  but **is not** the FY2026 DCF cash flow. Reported 9M OCF is not used as FCFF.
- Q4 2026 is discounted 0.25 years; FY2027–FY2030 are discounted 1.25, 2.25,
  3.25 and 4.25 years. This fixed schedule is date-specific.
- FY2031 terminal revenue = FY2030 revenue × (1 + g). Operating margin, tax,
  D&A and CapEx ratios remain at FY2030 levels; terminal change in NWC =
  FY2030 proxy NWC × g. Recompute terminal FCFF from those components.
- Terminal value at December 2030 = FY2031 FCFF / (WACC − g), discounted 4.25
  years. It is not simply FY2030 FCFF scaled by g, which would retain the wrong
  transition-year working-capital requirement.
- Enterprise value = PV of explicit future FCFF + PV of terminal value.
  WACC must exceed g; invalid, nonfinite or missing assumptions fail explicitly.

Constant terminal margins and reinvestment ratios are unvalidated steady-state
assumptions. Economic consistency with an achievable return on capital remains
open. Review terminal-value dependence in `scenario_dcf.csv`.

## Enterprise-to-equity bridge: blocked

The implemented formula is enterprise value + eligible excess cash + eligible
nonoperating investments − debt/debt-like claims − other equity claims; divide
by validated million diluted shares for USD per share. Every bridge input must
have explicit validation, correct units and a source reference at the same date.
Current inputs are deliberately null in `equity_bridge.json`, including amounts
that could eventually be justified as zero. Outputs carry specific blocking reasons.

Reported cash and securities do not automatically equal distributable excess
cash; no assumption of zero debt or other claims is made. Period weighted-average
EPS shares are not a validated point-in-time fully diluted valuation denominator.
Until classifications, dilution and adjustments are reviewed, equity value and
per-share values stay blank. Even a completed bridge would still be an illustrative
valuation until the operating and discount-rate assumptions are validated.

## Output tables and interpretation

`model_outputs/` contains assumptions/evidence requirements, historical inputs,
15 annual forecast rows, scenario DCF results, each forecast cash flow's discount
factor and present value, WACC/g sensitivities for each scenario, arithmetic
checks and an input hash manifest. Values and ratios use full computational
precision; output files serialize to ten significant digits. Figures are
illustrative enterprise values only, not stock-price targets.

### Illustrative scenario results — USD millions

| Scenario | FY2026 revenue (estimate) | FY2030 revenue (estimate) | Enterprise value | PV terminal / EV | Equity / per share |
| --- | ---: | ---: | ---: | ---: | --- |
| Base | 12,636.4 | 21,670.8 | 86,484.9 | 78.6% | BLOCKED |
| Bull | 13,134.0 | 29,018.0 | 154,717.2 | 83.9% | BLOCKED |
| Bear | 12,138.9 | 15,897.7 | 38,671.0 | 69.5% | BLOCKED |

### Base enterprise-value sensitivity — hypothetical, USD millions

Only WACC and terminal growth vary; no per-share sensitivity is available.

| WACC / terminal g | 2.0% | 2.5% | 3.0% | 3.5% | 4.0% |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8% | 104,569.5 | 112,637.2 | 122,318.4 | 134,151.0 | 148,941.7 |
| 9% | 89,132.8 | 94,797.7 | 101,406.7 | 109,217.3 | 118,590.1 |
| 10% | 77,570.0 | 81,730.3 | 86,484.9 | 91,971.0 | 98,371.4 |
| 11% | 68,589.3 | 71,750.2 | 75,306.3 | 79,336.5 | 83,942.4 |
| 12% | 61,415.4 | 63,882.0 | 66,622.6 | 69,685.7 | 73,131.6 |

## Unresolved inputs before any defensible recommendation

1. Evidence-based operating scenarios and the appropriate forecast horizon.
2. Annual/interim cash-intangible purchase scope, plus maintenance versus growth reinvestment.
3. Operating NWC classification, working-capital timing and terminal reinvestment economics.
4. Normalized operating taxes and D&A schedules; loss-shield and SBC/dilution treatment.
5. Dated WACC components, sustainable terminal growth and return-on-capital assumptions.
6. Same-date eligible excess cash/investments, debt/debt-like and other claims, and fully diluted shares.
7. A sourced market-price/date reference if an upside/downside comparison is later requested.

No defensible investment recommendation follows from the numerical examples alone.

## Local validation

The complete existing and new test suite passes **76 tests**, including 19 new
valuation cases. All 60 saved forecast arithmetic checks pass. Tests also verify
the stub cash-flow exclusion, normalized terminal reinvestment, sensitivity
direction, missing/invalid assumptions, blocked bridge inputs, synthetic bridge
arithmetic, reproducible saved outputs and input hashes. Original workbook and
annual CSV fingerprints remain unchanged.
