# Q3 / 9M 2026 dashboard and TTM income

This extension adds a separate `2026 Q3 / 9M 10-Q` view; it does not change the
original Excel, annual verified data or user CSV schema. Source data under
`data/quarterly/` remains unchanged from the extraction task. The previous
extraction report describes the checks and file state at that earlier stage.

## Sources and runtime gates

- [Official 2026 Form 10-Q](https://www.sec.gov/Archives/edgar/data/1596532/000159653226000254/anet-20260930.htm),
  filed November 4, 2026, reporting September 30, 2026. Part I Item 1 printed
  p.2: income; p.1: balance sheets; p.5: nine-month cash flows.
- Annual input: reviewed local `data/verified_2023_2025.csv`, from local 2025
  Form 10-K PDF p.73 (printed p.69).
  [Annual SEC URL](https://www.sec.gov/Archives/edgar/data/1596532/000159653226000013/anet-20251231.htm).
  This annual document was not independently authenticated online.

On opening the view, both interim source-capture hashes must match metadata;
every statement CSV and metric summary must reconcile to the retained official
rendering and arithmetic checks must pass. Annual inputs must match the reviewed
annual CSV fingerprint. These offline checks establish provenance to the captured
sources; they do not claim an external audit or check for later SEC amendments.
TTM calculations additionally require verified flags, source URLs and references,
USD millions, FY2025 and exactly one nine-month period for each of 2026 and 2025,
with January 1–September 30 dates. Invalid inputs leave results unavailable.
No duplicate period is selected arbitrarily. Missing amounts block each affected
metric independently, without imputing zero or blocking unrelated valid metrics.
Non-finite numeric values are rejected.

## Matched-period comparisons

YoY = current / prior − 1. Q3 compares July 1–September 30, 2026 with the same
2025 quarter. 9M compares January 1–September 30 for 2026 and 2025.
Missing values and nonpositive prior denominators leave growth blank. EPS growth
uses rounded reported diluted EPS, not an unrounded earnings-per-share estimate.
Amounts are USD millions except EPS (USD per share).

| Period type | Metric | 2026 | 2025 | YoY |
| --- | --- | ---: | ---: | ---: |
| Quarter (Q3) | revenue | 3,657.60 | 2,308.30 | 58.4543% |
| Quarter (Q3) | gross_profit | 2,325.70 | 1,490.20 | 56.0663% |
| Quarter (Q3) | operating_income | 1,642.40 | 978.20 | 67.9002% |
| Quarter (Q3) | net_income | 1,560.40 | 853.00 | 82.9308% |
| Quarter (Q3) | diluted_eps | 1.22 | 0.67 | 82.0896% |
| Nine months YTD (9M) | revenue | 9,402.30 | 6,517.90 | 44.2535% |
| Nine months YTD (9M) | gross_profit | 5,912.80 | 4,204.90 | 40.6169% |
| Nine months YTD (9M) | operating_income | 4,178.20 | 2,823.20 | 47.9952% |
| Nine months YTD (9M) | net_income | 3,796.20 | 2,555.60 | 48.5444% |
| Nine months YTD (9M) | diluted_eps | 2.98 | 2.00 | 49.0000% |

## TTM income: October 1, 2025–September 30, 2026

TTM = FY2025 + 9M2026 − 9M2025. This replaces the first nine months of FY2025
with the first nine months of 2026, leaving Q4 2025 plus 9M2026. It does not
annualize Q3 or 9M. These are analytical amounts from verified source inputs,
not a separately reported SEC TTM statement.

| Metric | FY2025 | +9M2026 | −9M2025 | TTM (USD millions) |
| --- | ---: | ---: | ---: | ---: |
| revenue | 9,005.7 | 9,402.3 | 6,517.9 | 11,890.1 |
| cost_of_revenue | 3,237.0 | 3,489.5 | 2,313.0 | 4,413.5 |
| gross_profit | 5,768.7 | 5,912.8 | 4,204.9 | 7,476.6 |
| operating_expenses | 1,912.6 | 1,734.6 | 1,381.7 | 2,265.5 |
| operating_income | 3,856.1 | 4,178.2 | 2,823.2 | 5,211.1 |
| net_income | 3,511.4 | 3,796.2 | 2,555.6 | 4,752.0 |

### Diluted EPS remains unavailable

Diluted EPS is not additive. Each reported period's EPS is rounded to cents,
and each uses a different diluted weighted-average share count. Even differences
of rounded FY and 9M EPS would inherit rounding error and would not establish the
correct TTM share denominator. The annual verified dataset does not provide a
validated TTM denominator. No TTM EPS number is presented or exported; its status
explains the additional share-count and rounding validation required. The view
still shows the four reported Q3/9M EPS figures and their rounded-basis growth.

## Nine-month cash flows and blocked TTM FCF

Only 9M cash flow is available: 9M2026 OCF 3,977.4 and signed PP&E purchases
(184.9), giving analytical PP&E-only FCF 3,792.5. 9M2025 OCF 3,110.0 and signed
PP&E purchases (82.5), giving analytical PP&E-only FCF 3,027.5 (USD millions).
FCF subtracts the positive outflow magnitude: OCF − abs(signed purchases).
Cash-flow YoY uses the same two nine-month periods and is assigned only to the
2026 comparison row; 2025 is the base and its growth stays blank.
No standalone Q3 operating cash flow or FCF is inferred.

TTM FCF is **not calculated**, including in exports. The annual cash-flow line
combines property, equipment and intangible purchases while the interim line
is PP&E-only. A matching annual/interim spending definition must be verified
before any TTM cash-flow calculation. The existing annual FCF series retains
its explicit inclusion of intangible purchases.

## Exports and limitations

Downloads include the ten matched-period comparisons, four interim metric rows
(including missing Q3 cash flow), the two 9M cash-flow rows, source statement
CSVs and the eight-row TTM analysis (six additive metrics plus blank EPS and
blocked FCF). Exports contain period labels, units, source URLs/references and
verification or limitation statuses. Ratios are numeric fractions in CSVs.
The source-data expander retains source labels/signs and balance-sheet dates.
The annual PDF does not contain a full 2023 balance sheet; the 10-Q balance-sheet
comparatives are September 30, 2026 and December 31, 2025, not September 30, 2025.

Tests cover TTM formulas with actual and synthetic inputs, per-input missing
values, verification/source/unit/date gates, absent or duplicated periods,
matching-duration growth, source tampering, UI period labels and exports, blank
TTM EPS/FCF, and switching back to existing annual/Excel modes. Both Excel
workbook hashes and the reviewed annual CSV hash remain protected. The old
extraction metadata's app.py hash is historical; the test now permits the
explicitly authorized dashboard integration without changing that metadata.
Run `.venv/bin/python -m pytest -q` from the repository root.
