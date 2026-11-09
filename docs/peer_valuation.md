# Comparable-company analysis — scoped, not a false precision cross-check

Research/market reference: November 8 / November 6, 2026. USD millions.
[Input register](../data/integrated/peer_inputs.json) records directly inspected
SEC statement figures, exact fiscal dates, source labels and short numeric extracts.
[Output table](../model_outputs/integrated/peer_comparison.csv) calculates growth
and GAAP operating margin. No consensus estimates or market multiples are invented.

| Company | Why included | Why consolidated valuation is imperfect |
| --- | --- | --- |
| ANET | Subject; cloud/data-center/campus networking | Concentrated customers; compare growth and margins without assuming a durable premium |
| Cisco | Direct networking competitor, identified in ANET 10-K Item 1 pp.8–9 | Broader software/security/services and acquisition effects; group economics are not pure-play AI Ethernet economics |
| NVIDIA | Ethernet/InfiniBand/NVLink platform alternatives, FY2026 10-K Item 1 p.5 | Compute-dominated consolidated business; networking is not independently valued here |

Historical anchors: ANET FY2025 ends December 31, 2025; Cisco FY2026 ends July 25,
2026; NVIDIA FY2026 ends January 25, 2026. Growth is each company's own annual
comparison, not a common calendar-period comparison. The table is not an aligned
TTM peer ranking. No conclusion about relative cheapness follows from it.

- [ANET 10-K](https://www.sec.gov/Archives/edgar/data/1596532/000159653226000013/anet-20251231.htm), income p.69.
- [Cisco 10-K](https://www.sec.gov/Archives/edgar/data/858877/000085887726000132/csco-20260725.htm), statements of operations p.57: revenue 63,325 versus 56,654; operating income 15,368. Cisco's cash-flow “Depreciation, amortization, and other” is not automatically pure D&A for EBITDA.
- [NVIDIA 10-K](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm), income p.51: revenue 215,938 versus 130,497; operating income 130,387. Consolidated metrics are not networking segment metrics.

## Trading-multiple framework

| Metric | Formula | Required evidence / current result |
| --- | --- | --- |
| EV / Revenue | Common-date market EV / calendarized TTM consolidated revenue | BLOCKED: peer prices, same-date share schedules and EV bridges not verified; interim roll-forward needed |
| EV / EBITDA | Same EV / consistently defined TTM EBIT + pure D&A | BLOCKED: EV and aligned EBITDA missing; do not add back SBC without matching treatment across peers |
| Forward P/E | Dated price / sourced NTM diluted EPS | BLOCKED: no reliable dated consensus/model NTM EPS package; do not substitute historical EPS or ANET hypothetical forecast |
| Revenue growth / operating margin | Matched-period growth / GAAP EBIT ÷ revenue | Available for own fiscal years only; acquisition and segment mix remain comparability limitations |

`safe_multiple()` gates missing inputs, unmatched common TTM periods, financials
published after the valuation date and unverified definitions. A November market
quote may use September TTM financials filed before that quote; financial period
end is not required to equal the market date. All peers need the same market date
and comparable TTM end, with explicit publication dates. No median, premium/discount, implied price or numerical
DCF cross-check is presented while these inputs are absent. Next: acquire the
same reference-date price and share/claims package for each peer; calendarize
TTM financials; reconcile EBITDA and SBC; use source-stamped NTM estimates only
if obtainable. Then discuss business mix and growth differences before assigning
any relative valuation weight. The current evidence cannot support that weight.
