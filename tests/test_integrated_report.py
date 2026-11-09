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
