# ANET-Equity-Research
Equity research and financial analysis of Arista Networks (ANET), including valuation models and a Python dashboard.

## Financial analysis dashboard (v1)

An annual statement analysis tool built with Python, pandas, Plotly and Streamlit.
The template deliberately contains headers only: no ANET financial figures or
investment recommendations are supplied. Valuation models are not implemented in v1.

### Existing Excel model integration

The default dashboard now reads the user's supplied
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
Cash flow and capex are absent, so FCF and FCF margin stay blank. The first year's
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

### Prepare verified annual data

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

`anet_research/financials.py` contains validation and calculations; `app.py` is the
interactive dashboard; `data/` holds the blank template; `tests/` covers arithmetic,
invalid inputs, missing values, and dashboard rendering. Numerical fixtures in
tests are explicitly synthetic and are not ANET financial data.
