# ANET Equity Research

A reproducible Arista Networks (NYSE: ANET) research portfolio by **Ya-Cheng Hsieh (Erica Hsieh)**: SEC-sourced financial analysis, a Python/Streamlit dashboard, FCFF DCF scenarios, sensitivity analysis and evidence-controlled investment research.

## Latest portfolio report

**[Read the 10-page integrated Equity Research & Scenario-Based DCF report](reports/ANET_Integrated_Equity_Research_v2.pdf)** · Research date: November 8, 2026 (US Eastern).

The report covers business and AI networking, financial performance, preliminary thesis/catalysts, Base/Bull/Bear enterprise valuations, peer operating comparisons and a twelve-month target/rating framework. **All scenario assumptions remain HYPOTHETICAL / NOT YET VALIDATED. Equity/per-share values, a twelve-month target and upside/downside remain BLOCKED; the conclusion is NOT RATED.** A corroborated dated price is context, not a recommendation. Trading multiples remain blocked where aligned inputs are missing.

[Editable v2 source](reports/anet_integrated_research.md) · [Build / validation guide](reports/INTEGRATED_README.md) · [Previous 8-page report (archived)](reports/archive/v1_ANET_Equity_Research_2026-11-08.pdf)

Only the latest PDF is kept directly in `reports/`; prior PDFs are preserved in `reports/archive/`. The [report directory guide](reports/README.md) documents both renderers.

### Evidence and valuation deliverables

- [Integrated methodology](docs/integrated_valuation_methodology.md): scoped direct SEC rechecks, classification policy, NWC/CapEx/SBC limits and unchanged scenario EVs.
- [Equity bridge ledger](model_outputs/integrated/bridge_classification_ledger.csv) and [diluted-share schedule](model_outputs/integrated/diluted_share_schedule.csv): reported components separated from unresolved valuation adjustments.
- [Assumption/evidence matrix](model_outputs/integrated/assumption_evidence_matrix.csv), [financial analysis](model_outputs/integrated/financial_analysis.csv) and [32 SEC figure rechecks](model_outputs/integrated/sec_rechecks.csv).
- [Peer analysis](docs/peer_valuation.md) and [comparison table](model_outputs/integrated/peer_comparison.csv): sourced annual growth/margins with explicit fiscal dates; no invented market/forward multiples.
- [Price target / rating methodology](docs/price_target_framework.md), [dated price evidence](data/integrated/market_reference.json), [readiness/blocker output](model_outputs/integrated/valuation_readiness.json) and [thesis / risk framework](docs/investment_framework.md).

**Validation: [136 tests passed and exact blockers](docs/integrated_validation.md).**

The September 30, 2026 DCF uses information filed later on November 4 and is retrospective. No validated stock target is claimed. The original workbooks, verified historical CSVs, original scenario figures, dashboard and previous report are preserved.

## Financial analysis dashboard

Built with Python, pandas, Plotly and Streamlit, the dashboard supports original
Excel analysis, user-attested CSV uploads, SEC-reviewed FY2023–FY2025 financials,
and Q3/9M2026 comparisons with additive TTM income analysis. The original v1
started as an annual CSV analysis tool with a headers-only template; that template
is still blank, while reviewed ANET data now resides in separate source files.
The current portfolio also includes the written report and standalone FCFF DCF
described below; the DCF is not a dashboard feature.

### Existing Excel model integration

The default **Excel mode** reads the user's supplied
`data/source/ANET_Financial Model.xlsx` in read-only fashion. Its historical figures
and every derived ratio are **UNVERIFIED**: the workbook has no SEC citations.
The blank CSV template remains unchanged. Select **Verified CSV** in the sidebar
to use the original, strict CSV validation workflow.

`anet_research/excel.py` supports the supplied `Historical Financials` layout,
2023–2025, USD millions. It recalculates revenue, gross profit, operating income
and ratios from literal inputs, validates the expected formula expressions, and
compares all 20 formulas against Excel's saved results. It does not execute Excel
formulas or fetch filings. Unexpected formulas/layouts fail explicitly; missing
inputs propagate, missing caches are reported as not comparable, and cache
differences are flagged. `=+C10/C4` is equivalent to `=C10/C4`.

The dashboard includes the original worksheet's cached values, cell-level formula
audit, charts, historical ratios, and exports carrying an unverified status and
worksheet references. SEC verification remains separate from arithmetic checks.
In Excel mode, cash flow and capex are absent, so FCF and FCF margin stay blank. The first year's
YoY stays blank because 2022 revenue is absent. See `docs/workbook_review.md`.

### Run locally

Use Python 3.12 (validated). From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit prints the local dashboard address. Stop with Ctrl+C.
No API keys, financial data downloads, or external services are required.

### Upload your own annual CSV

Copy `data/annual_financials_template.csv` to your own file, add annual rows, and
upload through the dashboard. Preserve the original blank template.

| Column | Convention |
| --- | --- |
| fiscal_year | Unique integer year; use consecutive fiscal years for YoY |
| revenue | Annual consolidated revenue, USD millions |
| gross_profit | Annual gross profit, USD millions |
| operating_income | Annual operating profit/loss, USD millions |
| net_income | Annual net profit/loss, USD millions |
| operating_cash_flow | Annual net cash from operating activities, USD millions |
| capital_expenditures | Annual capex, USD millions, entered as a positive cash outflow |
| source_url | HTTPS SEC filing URL under sec.gov or www.sec.gov |
| source_reference | Form 10-K year, page/table and any restatement or unit conversion notes |
| verified | `true` only after checking all populated values against the cited 10-K |

Leave financial fields blank until verified. Convert reported dollars/thousands
to USD millions consistently. Use consistent consolidated scope and restated
comparatives; document the chosen capex line items. Source fields and `verified`
are user attestations, not automatic SEC authentication or validation of figures.
Populated financial rows without this provenance are rejected. Blank values are
never imputed; negative earnings and operating cash flow are supported.

### Calculations

- Revenue YoY: current / prior revenue − 1, only for consecutive years with positive prior revenue.
- Gross, operating and net margins: corresponding profit / revenue.
- Free cash flow: operating cash flow − positive capital expenditures.
- FCF margin: free cash flow / revenue.

Margins require positive revenue. Missing inputs and undefined ratios stay blank.
Ratios are fractions in exported CSVs and percentages in charts. FCF is a derived
non-GAAP measure and may differ from company definitions. Year filters affect
display, while YoY uses the complete uploaded history.

### Tests and structure

```bash
python -m pytest -q
```

`anet_research/financials.py` contains annual validation and calculations; `app.py`
is the interactive dashboard. `data/` holds the original template, workbooks,
reviewed financial data and model inputs; `model_outputs/` holds reproducible
valuation tables; `reports/` holds the PDF and editable report source. Tests cover
synthetic calculation cases, reviewed ANET data, provenance, missing values,
dashboard rendering and valuation controls. Install `requirements-report.txt`
to include the optional PDF-generation and report-validation tests.

### Local 2025 Form 10-K verification extension

Select **Verified local 2025 Form 10-K** to load reviewed 2023–2025 figures from
`data/verified_2023_2025.csv`. The existing workbook and user-attested CSV modes
remain available with their original behavior; the earlier unverified descriptions
above apply to the workbook mode. No workbook or blank template was changed.

The local PDF has **107 pages**. The initial reconciliation checked income against
PDF p.73 (printed p.69) and cash flows against PDF p.76 (printed p.72). Subsequent
research and valuation reviews cross-checked the annual statements against the
official SEC filing; see the source register in the [research draft](docs/investment_thesis.md)
and [valuation evidence review](docs/valuation_evidence_review.md). These project
checks are not an independent audit. See
[the reconciliation report](docs/reconciliation_2023_2025.md) and its
[CSV](docs/reconciliation_2023_2025.csv) for Excel cells, SEC values, differences,
units, missing data, and page references. The report compares cached Excel results;
the existing loader separately checks their formulas and recomputation.

**FCF after property, equipment and intangible purchases** = operating cash flow
minus the absolute value of that combined purchase line. Its margin divides this
FCF by revenue. This is a derived non-GAAP measure that includes intangibles,
not traditional PP&E-only FCF. Signed purchases are retained in the source CSV;
the internal compatibility field `capital_expenditures` contains their absolute
outflow in this mode. Exports include the definition and source references.
The full 2023 balance sheet is unavailable; 2024–2025 balance sheets are present on
PDF p.72 but were not reconciled in the initial annual dashboard extension;
the later valuation evidence review derives selected balance-sheet/NWC proxies. Missing figures remain blank.
Tests now also include regression checks against locally reviewed ANET figures.

### Q3 / 9M 2026 Form 10-Q and TTM income

Select **2026 Q3 / 9M 10-Q** in the existing data-source selector. The default
Excel view, annual local 10-K view and user-attested CSV workflow are preserved.
Separate tabs compare Q3 2026 with Q3 2025 and 9M 2026 with 9M 2025, with revenue,
gross profit, operating income, net income, diluted EPS and matched-period YoY.
The nine-month cash-flow section is explicitly YTD; no Q3 cash flows are inferred.

`anet_research/interim.py` checks the saved official-source hashes, reconciles
all interim statement CSV rows and metrics to the captured filing, and checks
arithmetic before making data available to the view. Annual TTM inputs must
match the previously reviewed annual CSV fingerprint. Missing/unverified inputs,
invalid periods, incompatible units and duplicate required periods block the
corresponding TTM calculation. These are local provenance checks, not an SEC audit.

TTM income covers October 1, 2025–September 30, 2026 and uses
**FY2025 + 9M2026 − 9M2025**, with no annualization. Only additive USD-million
income metrics are calculated. TTM diluted EPS is deliberately unavailable:
reported EPS is rounded to cents and period-specific diluted weighted-average
share counts differ. Summing EPS or using the latest quarter's share count as
a TTM denominator is not validated. Reported Q3/9M EPS and its YoY growth remain
available, with a rounding caveat.

**TTM FCF is blocked** until annual and interim CapEx definitions are reconciled.
The annual series includes property, equipment **and intangible** purchases;
the 10-Q line is **purchases of property and equipment**. Only 9M PP&E-only
analytical FCF is shown. Its formula subtracts the purchase outflow magnitude,
while signed source values are preserved.

The view includes official source links, filing-page citations, provenance,
balance sheets, statement exports, matched-period growth exports, 9M cash-flow
exports and a separate TTM export with input amounts and explicit unavailable
statuses. Growth ratios are fractions in exports and percentages on screen.
See [the TTM methodology and results](docs/q3_2026_ttm_dashboard.md),
[the interim source reconciliation](docs/q3_2026_source_reconciliation.md), and
[the annual reconciliation](docs/reconciliation_2023_2025.md).

### Illustrative forecast and DCF (no dashboard changes)

A separate reproducible model now covers FY2026–FY2030. **All scenario assumptions
and enterprise-value outputs are HYPOTHETICAL / NOT YET VALIDATED**, not guidance,
a target price or a recommendation. FY2026 combines reported 9M income with a
modeled Q4; the September 30, 2026 reference-date DCF discounts Q4 only, then the
four subsequent forecast years. It is a retrospective analysis using the later-filed
10-Q, not a contemporaneous investment backtest.

```bash
python -m anet_research.valuation --output-dir model_outputs
python -m pytest -q
```

Edit only the explicitly labeled scenarios in `data/valuation/assumptions.json`;
`model_outputs/` contains forecast, scenario, sensitivity, assumptions, historical
input, arithmetic-check and discounting CSVs plus an input hash manifest.
See [valuation methodology and results](docs/forecast_dcf_methodology.md).

The annual cash purchase line includes intangibles; interim purchases are PP&E-only.
The model uses a separate hypothetical intangible reinvestment budget and never
splices the existing FCF series. Taxes and operating NWC classification remain
modeled. TTM FCF and TTM EPS remain unavailable. Equity and per-share outputs are
**BLOCKED** until excess-liquidity allocation, investment/nonoperating-asset
adjustments, aggregate debt/claims and point-in-time diluted-share inputs in
`data/valuation/equity_bridge.json` are supported. Reported cash and securities
are verified, but are not automatically excess liquidity. No current price is supplied.

### DCF evidence and bridge review (PR #4 follow-up)

See [the valuation evidence review](docs/valuation_evidence_review.md) for verified
September 2026 cash/securities and basic-share observations, unresolved excess-cash
allocation and dilution, reported/derived assumption evidence, CapEx alternatives,
NWC classifications and terminal reinvestment diagnostics. Re-running the same
valuation command also refreshes these review tables. The existing scenario
rates and enterprise values are unchanged; they are still hypothetical.
Equity/per-share output remains **BLOCKED** until operating liquidity, investment
adjustments, other nonoperating assets, aggregate claims and point-in-time dilution are supported. No
weighted-average EPS denominator is automatically accepted. No dashboard or
protected historical input was changed by that review. With report dependencies
installed, the earlier report-stage suite passed **90 tests**. The integrated upgrade adds
regression and report tests; see the latest validation guide linked above.
