# Local 2025 Form 10-K reconciliation, 2023–2025

Primary source: `anet-2025_10K.pdf` (107 pages). No outside sources used.
Income: PDF p.73 (printed p.69). Cash flows: PDF p.76 (printed p.72).
Amounts are USD millions; ratios below and in CSV are fractions unless shown as percentages.
Original root workbook and `data/source` copy are unchanged.

All 24 comparable income-statement amount cells match. Eleven comparable ratio
cells also match (derived from SEC amounts, not separately reported ratios).
Tolerance is 1e-8 in the row's units, allowing binary floating-point noise.
Difference = cached Excel value minus SEC amount or SEC-derived ratio.
2023 revenue growth is not comparable: 2022 revenue is unavailable.
The six cash-flow input values and six derived FCF/FCF-margin values are absent
from Excel. Missing Excel values and differences remain blank, never zero.
The original formula/cache audit remains a separate dashboard feature.

FCF after property, equipment and intangible purchases = operating cash flow −
absolute value of purchases of property, equipment and intangible assets.
This includes intangible purchases and is not traditional PP&E-only FCF.
The signed purchase line is retained; the generic internal `capital_expenditures`
field stores its absolute outflow solely for compatibility with existing calculations.
FCF is derived, non-GAAP; it is not a reported SEC line item.

The full 2023 balance sheet is unavailable. PDF p.72 (printed p.68) provides
2024–2025 balance sheets, which are outside this reconciliation's scope.
PP&E-only cash purchases are not separately disclosed in the combined cash-flow line.
No missing amounts are inferred from balance changes or project spending estimates.
Verification here means comparison against this local PDF, not independent authentication.

## FCF results

| Year | OCF | Signed combined purchases | FCF after property, equipment and intangible purchases | FCF margin |
| --- | ---: | ---: | ---: | ---: |
| 2023 | 2,034.0 | -34.4 | 1,999.6 | 34.1217% |
| 2024 | 3,708.2 | -32.0 | 3,676.2 | 52.4939% |
| 2025 | 4,371.9 | -119.5 | 4,252.4 | 47.2190% |

## Cell-level reconciliation

Exact machine-readable figures are in `reconciliation_2023_2025.csv`.

| Year | Metric | Excel cell | Excel | SEC / SEC-derived | Difference | Units | Status | PDF reference |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| 2023 | product_revenue | Historical Financials!B2 | 5029.5 | 5029.5 | 0 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2023 | service_revenue | Historical Financials!B3 | 830.7 | 830.7 | 0 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2023 | revenue | Historical Financials!B4 | 5860.2 | 5860.2 | 0 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2023 | revenue_growth_yoy | Historical Financials!B5 | — | — | — | fraction | MISSING / NOT COMPARABLE | PDF p.73 (printed p.69) |
| 2023 | cost_of_revenue | Historical Financials!B6 | 2229.9 | 2229.9 | 0 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2023 | gross_profit | Historical Financials!B7 | 3630.3 | 3630.3 | -4.547473509e-13 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2023 | gross_profit_margin | Historical Financials!B8 | 0.6194839767 | 0.6194839767 | -1.110223025e-16 | fraction | MATCH | PDF p.73 (printed p.69) |
| 2023 | operating_expenses | Historical Financials!B9 | 1373 | 1373 | 0 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2023 | operating_income | Historical Financials!B10 | 2257.3 | 2257.3 | -4.547473509e-13 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2023 | operating_profit_margin | Historical Financials!B11 | 0.3851916317 | 0.3851916317 | -1.110223025e-16 | fraction | MATCH | PDF p.73 (printed p.69) |
| 2023 | net_income | Historical Financials!B12 | 2087.3 | 2087.3 | 0 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2023 | net_profit_margin | Historical Financials!B13 | 0.3561823829 | 0.3561823829 | 0 | fraction | MATCH | PDF p.73 (printed p.69) |
| 2023 | operating_cash_flow | Not present | — | 2034 | — | USD millions | MISSING IN EXCEL | PDF p.76 (printed p.72) |
| 2023 | property_equipment_intangible_purchases | Not present | — | -34.4 | — | USD millions | MISSING IN EXCEL | PDF p.76 (printed p.72) |
| 2023 | free_cash_flow | Not present | — | 1999.6 | — | USD millions | MISSING IN EXCEL | PDF p.76 (printed p.72) |
| 2023 | free_cash_flow_margin | Not present | — | 0.3412170233 | — | fraction | MISSING IN EXCEL | PDF p.76 (printed p.72); p.73 revenue |
| 2024 | product_revenue | Historical Financials!C2 | 5884 | 5884 | 0 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2024 | service_revenue | Historical Financials!C3 | 1119.1 | 1119.1 | 0 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2024 | revenue | Historical Financials!C4 | 7003.1 | 7003.1 | 0 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2024 | revenue_growth_yoy | Historical Financials!C5 | 0.1950274735 | 0.1950274735 | 0 | fraction | MATCH | PDF p.73 (printed p.69) |
| 2024 | cost_of_revenue | Historical Financials!C6 | 2511.8 | 2511.8 | 0 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2024 | gross_profit | Historical Financials!C7 | 4491.3 | 4491.3 | 0 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2024 | gross_profit_margin | Historical Financials!C8 | 0.641330268 | 0.641330268 | 0 | fraction | MATCH | PDF p.73 (printed p.69) |
| 2024 | operating_expenses | Historical Financials!C9 | 1546.7 | 1546.7 | 0 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2024 | operating_income | Historical Financials!C10 | 2944.6 | 2944.6 | 4.547473509e-13 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2024 | operating_profit_margin | Historical Financials!C11 | 0.4204709343 | 0.4204709343 | 5.551115123e-17 | fraction | MATCH | PDF p.73 (printed p.69) |
| 2024 | net_income | Historical Financials!C12 | 2852.1 | 2852.1 | 0 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2024 | net_profit_margin | Historical Financials!C13 | 0.407262498 | 0.407262498 | 0 | fraction | MATCH | PDF p.73 (printed p.69) |
| 2024 | operating_cash_flow | Not present | — | 3708.2 | — | USD millions | MISSING IN EXCEL | PDF p.76 (printed p.72) |
| 2024 | property_equipment_intangible_purchases | Not present | — | -32 | — | USD millions | MISSING IN EXCEL | PDF p.76 (printed p.72) |
| 2024 | free_cash_flow | Not present | — | 3676.2 | — | USD millions | MISSING IN EXCEL | PDF p.76 (printed p.72) |
| 2024 | free_cash_flow_margin | Not present | — | 0.5249389556 | — | fraction | MISSING IN EXCEL | PDF p.76 (printed p.72); p.73 revenue |
| 2025 | product_revenue | Historical Financials!D2 | 7576.9 | 7576.9 | 0 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2025 | service_revenue | Historical Financials!D3 | 1428.8 | 1428.8 | 0 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2025 | revenue | Historical Financials!D4 | 9005.7 | 9005.7 | -1.818989404e-12 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2025 | revenue_growth_yoy | Historical Financials!D5 | 0.2859590753 | 0.2859590753 | -2.220446049e-16 | fraction | MATCH | PDF p.73 (printed p.69) |
| 2025 | cost_of_revenue | Historical Financials!D6 | 3237 | 3237 | 0 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2025 | gross_profit | Historical Financials!D7 | 5768.7 | 5768.7 | -9.094947018e-13 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2025 | gross_profit_margin | Historical Financials!D8 | 0.640560978 | 0.640560978 | 0 | fraction | MATCH | PDF p.73 (printed p.69) |
| 2025 | operating_expenses | Historical Financials!D9 | 1912.6 | 1912.6 | 0 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2025 | operating_income | Historical Financials!D10 | 3856.1 | 3856.1 | -9.094947018e-13 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2025 | operating_profit_margin | Historical Financials!D11 | 0.4281843721 | 0.4281843721 | 0 | fraction | MATCH | PDF p.73 (printed p.69) |
| 2025 | net_income | Historical Financials!D12 | 3511.4 | 3511.4 | 0 | USD millions | MATCH | PDF p.73 (printed p.69) |
| 2025 | net_profit_margin | Historical Financials!D13 | 0.3899086134 | 0.3899086134 | 5.551115123e-17 | fraction | MATCH | PDF p.73 (printed p.69) |
| 2025 | operating_cash_flow | Not present | — | 4371.9 | — | USD millions | MISSING IN EXCEL | PDF p.76 (printed p.72) |
| 2025 | property_equipment_intangible_purchases | Not present | — | -119.5 | — | USD millions | MISSING IN EXCEL | PDF p.76 (printed p.72) |
| 2025 | free_cash_flow | Not present | — | 4252.4 | — | USD millions | MISSING IN EXCEL | PDF p.76 (printed p.72) |
| 2025 | free_cash_flow_margin | Not present | — | 0.4721898353 | — | fraction | MISSING IN EXCEL | PDF p.76 (printed p.72); p.73 revenue |
