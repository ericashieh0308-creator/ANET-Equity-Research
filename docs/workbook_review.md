# Supplied workbook review

Original filename: `ANET_Financial Model.xlsx`. The uploaded attachment is retained;
an identical copy is stored under `data/source/`. Neither file is saved through
openpyxl or modified by the application.

SHA-256: `571b693f69a6644c5cab649b169f191ab404f69c90c8d55e733dd827c07ad5b3`

## Inventory and provenance

One worksheet: `Historical Financials`, A1:D13. B:D represent 2023–2025.
The explicit unit label is USD millions. All figures are **UNVERIFIED** because
the workbook contains no SEC URLs, filing references, or source verification.
No valuation, forecast, balance sheet, or cash flow worksheet is present.

| Rows | Existing work | Python treatment |
| --- | --- | --- |
| 2–3 | Product and service revenue literals | Sum to total revenue |
| 4 | Total revenue formula | Recompute from rows 2 + 3 |
| 5 | YoY revenue growth (2024–2025) | Current / previous − 1 |
| 6 | Cost of revenue literals | Input to gross profit |
| 7–8 | Gross profit and margin formulas | Revenue − cost; profit / revenue |
| 9 | Operating expenses literals | Input to operating income |
| 10–11 | Operating income and margin formulas | Gross profit − expenses; income / revenue |
| 12–13 | Net income literals and margin formulas | Net income / revenue |

All 20 saved formula results agree with independent Python arithmetic within
relative tolerance 1e-9 or absolute tolerance 1e-8. C11's `=+C10/C4` is equivalent
to division without unary plus. Agreement verifies arithmetic only, not accounting
scope, fiscal-year labeling, source accuracy, or subsequent restatements.

The importer supports this specific layout rather than arbitrary Excel models.
Unexpected formulas are rejected without execution. The dashboard audit exposes
original formula strings, cell addresses, cached values and recalculated results.
No historical inputs are silently replaced with estimates.

## Remaining work

1. Verify each year and line item against the appropriate SEC 10-K, documenting
   filing URLs, pages, scope, reported units and restatements.
2. Add verified operating cash flow and capex to support historical FCF. Obtain
   balance-sheet data, cash/debt and diluted share counts before equity valuation.
3. Develop explicitly sourced forecast assumptions, scenarios, a DCF (including
   discount rate, terminal value and sensitivity analysis), and peer valuation.
   No forecasts, prices, targets or recommendations were added in this integration.
4. Prepare the full research report: business and industry analysis, competitive
   position, historical performance, forecast rationale, valuation, catalysts,
   risks and citations. Conclusions require completed evidence and analysis.
