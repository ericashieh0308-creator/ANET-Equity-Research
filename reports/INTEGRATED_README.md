# Integrated report v2

- [Latest PDF](ANET_Integrated_Equity_Research_v2.pdf): ten A4 pages; Ya-Cheng Hsieh (Erica Hsieh); research date November 8, 2026, US Eastern.
- [Editable Markdown](anet_integrated_research.md), [builder](../scripts/build_integrated_report.py), [fingerprints](integrated_report_manifest.json).
- [Archived eight-page v1 PDF](archive/v1_ANET_Equity_Research_2026-11-08.pdf) and [archived source](archive/v1_anet_equity_research.md) are byte-identical to the previous versions. The original editable source and renderer remain available; the legacy builder now writes the PDF directly to the archive, and `report_manifest.json` records its current output path. The redundant root-level v1 PDF has been removed only after a byte-for-byte archive comparison. The archived v1 manifest is a baseline record, not the current integrated manifest; its paths are relative to the repository root at v1.

## Reproduce

```bash
python -m pip install -r requirements-report.txt
python -m anet_research.valuation --output-dir model_outputs
python -m anet_research.integrated
python scripts/build_integrated_report.py
python -m pytest -q
```

Run from the repository root, Python 3.12. The v2 renderer reuses the preserved v1
typography/charts and reads dedicated integrated schedules. ReportLab, PyMuPDF and
DejaVu Sans font requirements are unchanged; see [the original build guide](README.md).
No network is required to rebuild. New SEC and price observations are explicit
review records, not live feeds. Rebuilds refresh hashes and tests detect stale files.

## Review scope and limitations

The new work rechecks 24 annual and eight interim numbers against accessible official
SEC HTML, adds dated corroborated historical closes, fixes the explicit-date bridge
gap and adds claim-overlap, finite-value, dilution and rating gates. Ledger amounts
remain unknown where economic classifications are not supported. Forward assumptions
and original numerical scenarios are unchanged. Sourced peer operating figures use
separate fiscal periods and are not aligned trading valuations.

New material includes catalysts, thesis invalidation and a twelve-month horizon
framework, with NOT RATED and null target/upside until all evidence gates pass.
See [integrated methodology](../docs/integrated_valuation_methodology.md) for exact
source/assumption distinctions. Nothing in this report is a validated stock target.

## PDF validation

All ten pages are rendered and visually reviewed for glyphs, chart/table contrast,
clipping, overflow, blank pages and readable type. Automated tests validate page
bounds, counts, citations, displayed values, archive identity and deterministic
rebuild. Temporary preview images stay outside Git. Full suite: **136 passed**; see [validation and blockers](../docs/integrated_validation.md). Tests do not establish forecast or investment validity.
