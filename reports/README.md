# Portfolio report — build and review

- PDF: [ANET_Equity_Research_2026-11-08.pdf](ANET_Equity_Research_2026-11-08.pdf), eight A4 pages.
- Editable narrative/layout source: [anet_equity_research.md](anet_equity_research.md).
- Builder: [scripts/build_research_report.py](../scripts/build_research_report.py).
- Input/output fingerprints: [report_manifest.json](report_manifest.json).

From the repository root:

```bash
python -m pip install -r requirements-report.txt
python scripts/build_research_report.py
python -m pytest -q
```

The builder runs offline using the existing annual/interim CSVs and valuation outputs.
It does not rerun/recalibrate valuations or modify protected financial inputs.
The Markdown contains eight explicit page sections and named table/chart placeholders;
edit narrative there, and table/chart formatting in the builder. Monetary tables use
USD millions; EPS alone uses USD/share. Percentages and numbers are rounded only for
presentation. The PDF embeds DejaVu Sans/DejaVu Sans Bold; the builder expects these
fonts under `/usr/share/fonts/truetype/dejavu/` (Debian `fonts-dejavu-core`). Charts
are vector drawings. Report dependencies are optional and do not change dashboard dependencies.

The report starts from main commit `ef5c8b0` (which includes PR #4's evidence audit).
The requested research date is November 8, 2026; preparation includes the later
repository audit. The DCF is retrospectively referenced to September 30 using the
November 4 filing, not an investable backtest. Existing research draft Section 6's
older “not yet developed” valuation status is superseded for this report by the
existing forecast methodology/evidence audit, not treated as current model status.
Internal PDF source links are pinned to that main baseline for reproducibility.
Official SEC URLs and printed filing page/section locations are preserved from
the sourced draft and evidence audit; no new external claims or downloads are introduced.

## Validation

Automated report tests check the eight-page structure, required disclosures, source
URLs, table values, readable white header glyphs, embedded fonts, page boundaries,
input/output hashes and deterministic rebuild. The complete financial model suite
continues to apply. Final validation: **90 tests passed**, including three PDF/report tests. Install the report dependencies to run these tests; they skip
explicitly when optional PDF packages are absent.

Rendered all eight pages at native A4 size and inspected each, including the
forecast, scenario/sensitivity and source tables. Checked table wrapping, contrast,
glyphs, margins, chart labels, blank pages and overflow. No rendering defects remain
in the reviewed PDF. Raster inspection files live only in `/tmp`, not in the PR.

All unsupported forward drivers remain HYPOTHETICAL / NOT YET VALIDATED. The equity
bridge remains BLOCKED for excess-liquidity allocation, investment/nonoperating-asset
adjustments, aggregate claims classification and point-in-time dilution. Numerical
scenario enterprise values are not equity values, recommendations or stock targets.
