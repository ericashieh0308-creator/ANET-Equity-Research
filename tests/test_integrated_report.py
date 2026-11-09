"""Integrated PDF and archived-report regression checks."""

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

import pandas as pd
import pytest

pdf = pytest.importorskip("pymupdf", reason="Install requirements-report.txt")
pytest.importorskip("reportlab", reason="Install requirements-report.txt")
ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "reports/ANET_Integrated_Equity_Research_v2.pdf"


def test_integrated_pdf_pages_bounds_text_and_sources():
    d = pdf.open(PATH)
    assert len(d) == 10
    full = " ".join(" ".join(p.get_text().split()) for p in d)
    for n, page in enumerate(d):
        assert len(page.get_text()) > 1500
        assert f"{n+1} / 10" in page.get_text() and f"{n+1} / 8" not in page.get_text()
        assert not any(
            x in page.get_text() for x in ["\ufffd", "\u25a0", "{{", "---PAGE---"]
        )
        for b in page.get_text("dict")["blocks"]:
            for line in b.get("lines", []):
                for s in line["spans"]:
                    x0, y0, x1, y1 = s["bbox"]
                    assert 40 <= x0 < x1 <= 556 and 12 <= y0 < y1 <= 824, s
    for required in [
        "NOT RATED",
        "170.80",
        "November 6, 2026",
        "November 8, 2027",
        "HYPOTHETICAL / NOT YET VALIDATED",
        "retrospective",
        "period averages",
        "Trading multiples",
        "calendarized",
        "No TTM diluted EPS",
    ]:
        assert required in full
    assert "No current price or per-share result is supplied" not in full
    urls = {link.get("uri") for p in d for link in p.get_links() if link.get("uri")}
    assert len(urls) == 10
    assert len([u for u in urls if u.startswith("https://www.sec.gov/Archives/")]) == 4
    peers = pd.read_csv(ROOT / "model_outputs/integrated/peer_comparison.csv")
    for r in peers.itertuples():
        assert f"{r.revenue:,.1f}" in full and r.period_end in full
        assert f"{r.operating_margin*100:.1f}%" in full
    assert "Thesis monitoring and twelve-month framework" in full


def test_archive_identity_manifest_and_rebuild():
    for name in [
        "ANET_Equity_Research_2026-11-08.pdf",
        "anet_equity_research.md",
        "report_manifest.json",
    ]:
        assert (ROOT / "reports" / name).read_bytes() == (
            ROOT / "reports/archive" / ("v1_" + name)
        ).read_bytes()
    manifest = json.loads(
        (ROOT / "reports/integrated_report_manifest.json").read_text()
    )
    for path, digest in manifest["input_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
    before = PATH.read_bytes()
    assert hashlib.sha256(before).hexdigest() == manifest["pdf_sha256"]
    subprocess.run(
        [sys.executable, "scripts/build_integrated_report.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    assert PATH.read_bytes() == before


def test_new_documentation_links():
    names = [
        "README.md",
        "reports/INTEGRATED_README.md",
        "docs/integrated_valuation_methodology.md",
        "docs/peer_valuation.md",
        "docs/price_target_framework.md",
        "docs/investment_framework.md",
    ]
    for name in names:
        p = ROOT / name
        for url in re.findall(r"\[[^\]]*\]\(([^)]+)\)", p.read_text()):
            if url.startswith("http"):
                assert url.startswith("https://")
            elif not url.startswith("#"):
                assert (p.parent / url.split("#")[0]).is_file(), (name, url)


def test_executive_highlights_use_matched_nine_month_periods():
    from scripts.build_integrated_report import financial_highlight_rows

    assert financial_highlight_rows() == [
        ["Revenue", "9,402.3", "+44.3%"],
        ["Operating income", "4,178.2", "+48.0%"],
        ["Gross margin", "62.9%", "-1.6 pp"],
        ["Operating margin", "44.4%", "+1.1 pp"],
        ["Operating cash flow (OCF)", "3,977.4", "+27.9%"],
    ]
    first = " ".join(pdf.open(PATH)[0].get_text().split())
    assert "match 9M2026 with 9M2025" in first
    for row in financial_highlight_rows():
        assert " ".join(row) in first
    assert "OCF growth lagged revenue growth" in first


def test_price_availability_and_limitations_consistent():
    doc = pdf.open(PATH)
    front = " ".join(doc[0].get_text().split())
    target = " ".join(doc[8].get_text().split())
    limitations = " ".join(doc[9].get_text().split())
    assert "USD 170.80/share on November 6, 2026" in front
    assert "reference close is USD 170.80/share" in target
    assert "reference close is verified and available" in limitations
    assert "supported target numerator is still missing" in target
    assert "NOT RATED is not Hold" in target
    assert "equity/per-share outputs BLOCKED" in limitations
    assert "USD 203.59/share" in target  # September price is separate context.


def test_editorial_charts_show_units_direct_values_and_no_clipping():
    doc = pdf.open(PATH)
    annual = " ".join(doc[2].get_text().split())
    cash = " ".join(doc[3].get_text().split())
    assert "Reported revenue | USD millions" in annual
    assert "Derived operating margin | %" in annual
    assert all(x in annual for x in ["38.5%", "42.0%", "42.8%", "10,000"])
    assert "9M2026 YoY growth | analyst-derived, %" in cash
    assert all(x in cash for x in ["44.3%", "27.9%", "25.3%", "PP&E-only FCF"])
    # Font extents catch chart-label spillover that simple page counts miss.
    for n in [2, 3]:
        for b in doc[n].get_text("dict")["blocks"]:
            for line in b.get("lines", []):
                for span in line["spans"]:
                    assert span["bbox"][2] <= 549


def test_financial_tables_and_valuation_labels_match_source_pages():
    doc = pdf.open(PATH)
    pages = [" ".join(page.get_text().split()) for page in doc]
    annual = pd.read_csv(ROOT / "data/verified_2023_2025.csv")
    interim = pd.read_csv(ROOT / "data/quarterly/anet_20260930_metrics.csv")
    for frame in [annual, interim]:
        for key in ["revenue", "gross_profit", "operating_income", "net_income"]:
            for value in frame[key]:
                assert f"{value:,.1f}" in pages[2]
    forecasts = pd.read_csv(ROOT / "model_outputs/forecasts.csv")
    for key in [
        "revenue",
        "operating_income",
        "modeled_operating_taxes",
        "nopat",
        "da",
        "ppe_capex",
        "annual_fcff",
        "dcf_included_fcff",
    ]:
        for value in forecasts.loc[forecasts.scenario.eq("Base"), key]:
            assert f"{value:,.1f}" in pages[5]
    values = pd.read_csv(ROOT / "model_outputs/scenario_dcf.csv")
    grid = pd.read_csv(ROOT / "model_outputs/sensitivity.csv")
    for value in values.enterprise_value:
        assert f"{value:,.1f}" in pages[6]
    for value in grid.loc[grid.scenario.eq("Base"), "enterprise_value"]:
        assert f"{value:,.1f}" in pages[6]
    assert values.equity_value.isna().all() and values.value_per_share.isna().all()
    for page in [pages[4], pages[5], pages[6]]:
        assert "HYPOTHETICAL / NOT YET VALIDATED" in page
    assert "Q4 FY2026" in pages[5] and "0.25 years" in pages[5]
    assert "PP&E-only" in pages[3] and "intangibles" in pages[3]
    assert "not market capitalizations or equity valuations" in pages[6]
