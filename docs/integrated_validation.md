# Integrated upgrade — validation and remaining blockers

Baseline: main `6c1498f`; feature branch `codex/anet-integrated-research-v2`.
Research date: November 8, 2026 (US Eastern).

## Validation

- Complete suite: **132 passed**, including financial/dashboard, provenance,
  FCFF/DCF, new dates/claims/dilution/rating controls and original/integrated PDF tests.
- Dedicated SEC recheck: 24 annual + eight interim figures, all zero differences;
  this is scoped direct HTML inspection, not an independent audit of all data.
- Existing 60 forecast arithmetic checks and all three annual-to-Q4 stub
  reconciliations pass. Forecast, scenario EV, sensitivity and assumption files
  remain byte-identical to main; no new calibration is implied.
- Original Excel workbooks, verified annual/interim data, dashboard, original
  report/source/renderer remain byte-identical to main. The archived PDF/source
  are identical copies; integrated output has a separate manifest and filename.
- Both PDFs reproduce deterministically. Ten integrated pages were rendered and
  visually reviewed; automated bounds/glyph/value/source checks pass. No blank
  pages, clipping, overflow or missing glyphs observed.
- All 51 local links across the updated README and new build/methodology/thesis/
  peer/rating documents resolve. Official SEC and price pages were opened during
  the source review; link checking is not proof that third-party data never changes.
- `git diff --check` passes. No credentials, source downloads, temporary previews
  or unrelated artifacts are included; the PDFs are approximately 90–105 KB each.

## Exact outstanding decisions

| Output | Why BLOCKED | Required next evidence |
| --- | --- | --- |
| Equity Value | Reported cash/securities are not excess liquidity; other asset/claim aggregates lack economic classifications | Justify operating reserve and investment eligibility/tax adjustments; classify 899.2 other assets and 296.4 / 358.1 current/long-term other liabilities; prevent NWC/claims overlap |
| Point-in-time diluted shares / per-share value | Basic shares and gross RSUs do not establish complete economic dilution | Award/option/ESPP population, vesting/performance conditions, justified proceeds and remaining-service/SBC policy; dated price is now available but insufficient alone |
| Defensible DCF fair value | All forward driver choices and discount/terminal assumptions remain hypothetical | Demand/mix/cost/tax/reinvestment/NWC calibration; sourced WACC components and a sustainable terminal growth/reinvestment/return argument |
| Twelve-month target / upside-downside | No supported equity/per-share value or forward-horizon capital/FCFF/share schedule | Revalue at November 8, 2027 horizon; align reference date, distributions, cash, claims and dilution. Do not roll equity price at WACC |
| Buy/Hold/Sell | Economic gates incomplete; analyst return hurdles intentionally unset | Document policy thresholds/risk rationale and pass valuation gates. Current status NOT RATED, not Hold |
| Trading comps / DCF peer cross-check | Peer consolidated operating periods differ; market and forward inputs incomplete | Same-date market caps/EV bridges; calendarized TTM revenue and consistently defined EBITDA; reliable dated NTM EPS |

Annual combined property/equipment/intangible purchases cannot be numerically
split from current evidence; interim purchases remain PP&E-only. CapEx alternatives
stay separate; no unsupported TTM FCF or diluted EPS is introduced. A sourced price
and correct arithmetic do not validate forward assumptions or a target.
