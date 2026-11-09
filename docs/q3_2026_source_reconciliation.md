# ANET Q3 2026 Form 10-Q extraction and source reconciliation

Primary source: [complete official Form 10-Q](https://www.sec.gov/Archives/edgar/data/1596532/000159653226000254/anet-20260930.htm).
[SEC filing detail](https://www.sec.gov/Archives/edgar/data/1596532/000159653226000254/0001596532-26-000254-index.html): accession 0001596532-26-000254,
report period September 30, 2026, **filing date November 4, 2026**;
accepted November 3, 2026 at 18:50:52. Acceptance/signature dates are not the filing date.

## Scope and provenance

The complete web-rendered official 10-Q (cover, statements and notes, MD&A,
risk factors, exhibits index and signatures through printed p.56) was retrieved
and reviewed. Complete line coverage 0–1909 is retained in
`data/quarterly/anet_20260930_source.txt`. This is a web-reader text rendering,
**not raw SEC HTML**, an SEC-certified copy, or a PDF. The execution environment's
direct HTTP download was denied; the official document was accessible through
the web reader via EDGAR's filing directory. No earnings release or third-party
financial dataset was used. Tool-rendered layout/whitespace may differ from HTML;
source labels and displayed numeric tokens are retained in the extraction.

The metadata JSON records official URLs, filing dates, snapshot SHA-256 digests,
page locations and protected-file hashes. Line numbers are local snapshot
locators, not SEC page numbers. Pages below are filing printed pages.
All extracted values have statement, section, source label, source display value,
normalized signed decimal, financial units, period start/end and duration,
column index, source line/page, URL and accession. A literal source dash means
reported nil (numeric zero), not an absent observation. Parentheses mean negative.
EPS retains USD per share; weighted-average shares retain millions of shares;
statement amounts retain USD millions. Balance sheet par value/shares embedded
in source labels are not reinterpreted as the financial amount column.
The December 2025 balance sheet derives from audited annual accounts; the
interim presentation is condensed (Note 1, printed p.6).

## Reconciliation result

All **190 extracted reported values** (80 income, 52 balance-sheet, 58 cash-flow)
match the preserved official-source numeric tokens, labels, column order and periods.
Automated source checks compare every CSV row against re-extraction from the
hashed snapshot. They establish local traceability, not an independent SEC audit.
The saved metrics file is checked against the statement records separately.

The arithmetic report `docs/q3_2026_arithmetic_checks.csv` contains
**56 checks**: {'PASS': 52, 'ROUNDING': 4}.
All amount-based identities reconcile exactly at displayed precision, including
revenue/cost splits, gross/operating/pretax/net income, balance-sheet totals,
operating/investing/financing cash flow, net cash change and cash roll-forwards.
Income-statement and cash-flow net income agree for both 9M periods.
The four EPS ratios agree after rounding to cents; their unrounded differences
are explicitly shown rather than treating EPS as an exact division.
No financial discrepancies were found. Printed-amount rounding bounds are
0.05 million per operand plus the reported result; EPS tolerance is 0.0051 USD/share
(half a cent plus allowance for rounded printed net income/share counts).
These tolerances do not change source values. `DISCREPANCY` is distinct from `ROUNDING`.

## Missing values and period limits

Income has Q3 2026/Q3 2025 and 9M 2026/9M 2025 columns (printed p.2).
Balance sheets are at September 30, 2026 and December 31, 2025 (printed p.1);
September 30, 2025 is not a balance-sheet comparative in this filing.
Cash flows contain **nine-month YTD amounts only** (printed p.5).
Standalone Q3 operating cash flow, PP&E purchases and FCF remain blank and
explicitly marked NOT REPORTED. No Q3 cash-flow estimates, annualization,
or subtraction from 9M alone was performed. Q3 balance-sheet operating flows
are not meaningful stock measures and are not populated.

## Analytical FCF, kept separate from annual data

Analytical FCF after purchases of property and equipment (PP&E-only)
= operating cash flow minus the **positive spending magnitude** of PP&E purchases.
Source purchases retain negative signs; equivalent arithmetic is OCF plus the
signed purchase line. Subtracting the signed negative value would incorrectly
increase FCF. This is an analytical non-GAAP measure, not an SEC-reported FCF line.
It is **not** the existing 2023–2025 FCF after property, equipment and intangible
purchases. The two definitions are neither merged nor silently relabeled.

| Period | OCF | Signed PP&E purchases | PP&E spending magnitude | Analytical PP&E-only FCF |
| --- | ---: | ---: | ---: | ---: |
| Q3 2026 | Not reported | Not reported | Not reported | Not reported |
| Q3 2025 | Not reported | Not reported | Not reported | Not reported |
| 9M 2026 | 3977.4 | -184.9 | 184.9 | 3792.5 |
| 9M 2025 | 3110.0 | -82.5 | 82.5 | 3027.5 |

## Complete extracted statement tables

Displayed source tokens below preserve parentheses, dashes and decimal precision.

### Condensed Consolidated Income Statements — printed p.2

(Unaudited, in millions, except per share amounts)

| Section / source label | Q3 2026 | Q3 2025 | 9M 2026 | 9M 2025 | Snapshot line |
| --- | ---: | ---: | ---: | ---: | --- |
| Revenue: / Product | 3,190.0 | 1,911.7 | 8,106.5 | 5,481.2 | L168 |
| Revenue: / Service | 467.6 | 396.6 | 1,295.8 | 1,036.7 | L169 |
| Revenue: / Total revenue | 3,657.6 | 2,308.3 | 9,402.3 | 6,517.9 | L170 |
| Cost of revenue: / Product | 1,255.1 | 745.5 | 3,264.5 | 2,125.5 | L172 |
| Cost of revenue: / Service | 76.8 | 72.6 | 225.0 | 187.5 | L173 |
| Cost of revenue: / Total cost of revenue | 1,331.9 | 818.1 | 3,489.5 | 2,313.0 | L174 |
| Cost of revenue: / Gross profit | 2,325.7 | 1,490.2 | 5,912.8 | 4,204.9 | L175 |
| Operating expenses: / Research and development | 486.9 | 326.0 | 1,178.8 | 888.9 | L177 |
| Operating expenses: / Sales and marketing | 156.6 | 151.2 | 448.5 | 394.3 | L178 |
| Operating expenses: / General and administrative | 39.8 | 34.8 | 107.3 | 98.5 | L179 |
| Operating expenses: / Total operating expenses | 683.3 | 512.0 | 1,734.6 | 1,381.7 | L181 |
| Operating expenses: / Income from operations | 1,642.4 | 978.2 | 4,178.2 | 2,823.2 | L182 |
| Operating expenses: / Other income (expense), net | 273.1 | 98.9 | 513.0 | 289.1 | L183 |
| Operating expenses: / Income before income taxes | 1,915.5 | 1,077.1 | 4,691.2 | 3,112.3 | L184 |
| Operating expenses: / Provision for income taxes | 355.1 | 224.1 | 895.0 | 556.7 | L185 |
| Operating expenses: / Net income | 1,560.4 | 853.0 | 3,796.2 | 2,555.6 | L186 |
| Net income per share: / Basic | 1.24 | 0.68 | 3.01 | 2.03 | L188 |
| Net income per share: / Diluted | 1.22 | 0.67 | 2.98 | 2.00 | L189 |
| Weighted-average shares used in computing net income per share: / Basic | 1,262.2 | 1,258.0 | 1,260.0 | 1,258.1 | L191 |
| Weighted-average shares used in computing net income per share: / Diluted | 1,278.2 | 1,276.6 | 1,276.0 | 1,275.7 | L192 |

### Condensed Consolidated Balance Sheets — printed p.1

(In millions, except par value)

| Section / source label | 2026-09-30 | 2025-12-31 | Snapshot line |
| --- | ---: | ---: | --- |
| CURRENT ASSETS: / Cash and cash equivalents | 2,288.1 | 1,963.9 | L110 |
| CURRENT ASSETS: / Marketable securities | 12,070.9 | 8,779.1 | L111 |
| CURRENT ASSETS: / Accounts receivable, net | 2,327.8 | 1,886.9 | L112 |
| CURRENT ASSETS: / Inventories | 3,209.8 | 2,247.1 | L113 |
| CURRENT ASSETS: / Prepaid expenses and other current assets | 2,235.7 | 1,510.0 | L114 |
| CURRENT ASSETS: / Total current assets | 22,132.3 | 16,387.0 | L115 |
| CURRENT ASSETS: / Property and equipment, net | 378.8 | 203.1 | L116 |
| CURRENT ASSETS: / Goodwill | 416.1 | 416.1 | L118 |
| CURRENT ASSETS: / Deferred tax assets | 1,437.7 | 1,773.6 | L121 |
| CURRENT ASSETS: / Other assets | 899.2 | 668.8 | L122 |
| CURRENT ASSETS: / TOTAL ASSETS | 25,264.1 | 19,448.6 | L123 |
| CURRENT LIABILITIES: / Accounts payable | 682.6 | 651.7 | L126 |
| CURRENT LIABILITIES: / Accrued liabilities | 640.8 | 475.4 | L127 |
| CURRENT LIABILITIES: / Deferred revenue | 5,102.2 | 4,002.6 | L129 |
| CURRENT LIABILITIES: / Other current liabilities | 296.4 | 246.8 | L132 |
| CURRENT LIABILITIES: / Total current liabilities | 6,722.0 | 5,376.5 | L133 |
| CURRENT LIABILITIES: / Deferred revenue, non-current | 1,737.3 | 1,369.8 | L136 |
| CURRENT LIABILITIES: / Other long-term liabilities | 358.1 | 331.8 | L138 |
| CURRENT LIABILITIES: / TOTAL LIABILITIES | 8,817.4 | 7,078.1 | L139 |
| STOCKHOLDERS’ EQUITY: / Preferred stock, $0.0001 par value—100 shares authorized and no shares issued and outstanding as of September 30, 2026 and December 31, 2025 | — | — | L142 |
| STOCKHOLDERS’ EQUITY: / Common stock, $0.0001 par value—4,000 shares authorized as of September 30, 2026 and December 31, 2025; 1,263.4 and 1,256.5 shares issued and outstanding as of September 30, 2026 and December 31, 2025 | 0.1 | 0.1 | L143 |
| STOCKHOLDERS’ EQUITY: / Additional paid-in capital | 3,304.4 | 2,911.8 | L144 |
| STOCKHOLDERS’ EQUITY: / Retained earnings | 13,243.2 | 9,446.6 | L145 |
| STOCKHOLDERS’ EQUITY: / Accumulated other comprehensive income (loss) | (101.0) | 12.0 | L146 |
| STOCKHOLDERS’ EQUITY: / TOTAL STOCKHOLDERS’ EQUITY | 16,446.7 | 12,370.5 | L147 |
| STOCKHOLDERS’ EQUITY: / TOTAL LIABILITIES AND STOCKHOLDERS’ EQUITY | 25,264.1 | 19,448.6 | L148 |

### Condensed Consolidated Statements of Cash Flows — printed p.5

(Unaudited, in millions)

| Section / source label | 9M 2026 | 9M 2025 | Snapshot line |
| --- | ---: | ---: | --- |
| CASH FLOWS FROM OPERATING ACTIVITIES: / Net income | 3,796.2 | 2,555.6 | L300 |
| Adjustments to reconcile net income to net cash provided by operating activities: / Depreciation and amortization | 70.3 | 49.8 | L302 |
| Adjustments to reconcile net income to net cash provided by operating activities: / Stock-based compensation | 379.4 | 306.1 | L303 |
| Adjustments to reconcile net income to net cash provided by operating activities: / Deferred income taxes | 369.3 | (202.5) | L304 |
| Adjustments to reconcile net income to net cash provided by operating activities: / Other | (148.2) | (23.5) | L305 |
| Changes in operating assets and liabilities: / Accounts receivable, net | (440.9) | (348.9) | L307 |
| Changes in operating assets and liabilities: / Inventories | (962.8) | (321.1) | L308 |
| Changes in operating assets and liabilities: / Other assets | (604.2) | (683.7) | L309 |
| Changes in operating assets and liabilities: / Accounts payable | 19.9 | 98.1 | L310 |
| Changes in operating assets and liabilities: / Deferred revenue | 1,467.1 | 1,765.7 | L311 |
| Changes in operating assets and liabilities: / Income taxes, net | (159.9) | (105.2) | L312 |
| Changes in operating assets and liabilities: / Other liabilities | 191.2 | 19.6 | L313 |
| Changes in operating assets and liabilities: / Net cash provided by operating activities | 3,977.4 | 3,110.0 | L314 |
| CASH FLOWS FROM INVESTING ACTIVITIES: / Proceeds from maturities of marketable securities | 2,437.7 | 2,590.3 | L316 |
| CASH FLOWS FROM INVESTING ACTIVITIES: / Proceeds from sale of marketable securities | 598.0 | 41.4 | L317 |
| CASH FLOWS FROM INVESTING ACTIVITIES: / Purchases of marketable securities | (6,449.9) | (4,816.3) | L318 |
| CASH FLOWS FROM INVESTING ACTIVITIES: / Purchases of property and equipment | (184.9) | (82.5) | L319 |
| CASH FLOWS FROM INVESTING ACTIVITIES: / Cash paid for business combinations, net of cash acquired | — | (300.0) | L320 |
| CASH FLOWS FROM INVESTING ACTIVITIES: / Other | (60.0) | (10.0) | L321 |
| CASH FLOWS FROM INVESTING ACTIVITIES: / Net cash used in investing activities | (3,659.1) | (2,577.1) | L322 |
| CASH FLOWS FROM FINANCING ACTIVITIES: / Proceeds from issuance of common stock under equity plans | 62.9 | 56.9 | L325 |
| CASH FLOWS FROM FINANCING ACTIVITIES: / Tax withholding paid on behalf of employees for net share settlement | (49.7) | (44.3) | L326 |
| CASH FLOWS FROM FINANCING ACTIVITIES: / Repurchases of common stock | — | (983.0) | L327 |
| CASH FLOWS FROM FINANCING ACTIVITIES: / Other | (3.7) | — | L328 |
| CASH FLOWS FROM FINANCING ACTIVITIES: / Net cash provided by (used in) financing activities | 9.5 | (970.4) | L329 |
| CASH FLOWS FROM FINANCING ACTIVITIES: / Effect of exchange rate changes | (3.5) | 1.7 | L330 |
| CASH FLOWS FROM FINANCING ACTIVITIES: / NET INCREASE (DECREASE) IN CASH, CASH EQUIVALENTS AND RESTRICTED CASH | 324.3 | (435.8) | L331 |
| CASH FLOWS FROM FINANCING ACTIVITIES: / CASH, CASH EQUIVALENTS AND RESTRICTED CASH —Beginning of period | 1,965.3 | 2,763.8 | L332 |
| CASH FLOWS FROM FINANCING ACTIVITIES: / CASH, CASH EQUIVALENTS AND RESTRICTED CASH —End of period | 2,289.6 | 2,328.0 | L333 |

## Reproduce and validate

Validation result: **37 tests passed**, including all 26 existing tests and
11 new quarterly cases. No existing tracked project file was modified.

From the repository root, run `.venv/bin/python -m pytest -q`.
`anet_research/quarterly.py` is an offline, fixed-layout parser and validator for
this captured filing. It is deliberately separate from annual validation and
from Streamlit; it does not infer unavailable periods. No network is needed for tests.
The source capture is an audit input; refresh/review it explicitly if the SEC
filing or web-reader layout changes. SHA checks detect local snapshot changes,
not future changes on the SEC website.

Both original Excel files, annual verified data, and the dashboard remain unchanged.
No commits, pushes, merges or publication were performed in this extraction task.
