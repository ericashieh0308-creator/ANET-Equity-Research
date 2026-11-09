"""Offline v2 report, preserving the original eight-page source and renderer."""

from pathlib import Path
import hashlib
import json
import re
import sys
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import build_research_report as base
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

SOURCE = ROOT / "reports/anet_integrated_research.md"
PDF = ROOT / "reports/ANET_Integrated_Equity_Research_v2.pdf"
TOTAL = 10
URLS = dict(base.URLS)
URLS.update(
    C="https://www.sec.gov/Archives/edgar/data/858877/000085887726000132/csco-20260725.htm",
    M="https://stockanalysis.com/stocks/anet/history/",
    U="https://github.com/ericashieh0308-creator/ANET-Equity-Research/blob/codex/anet-integrated-research-v2/docs/integrated_valuation_methodology.md",
)


def paragraph(text):
    text = escape(text)
    text = re.sub(
        r"\b(R[1-4]|K|Q|N|C|M|U)\b(?=[,;\]– /])",
        lambda m: '<a href="' + URLS[m[0]] + '" color="#147D85">' + m[0] + "</a>",
        text,
    )
    return Paragraph(text, base.style())


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(base.TEAL)
    canvas.setLineWidth(0.6)
    canvas.line(46, 807, 549, 807)
    canvas.setFont("Body", 7.2)
    canvas.setFillColor(base.GRAY)
    canvas.drawString(46, 818, "ANET | INTEGRATED EQUITY RESEARCH & SCENARIO-BASED DCF")
    canvas.drawString(
        46, 30, "Ya-Cheng Hsieh (Erica Hsieh) | November 8, 2026 | Portfolio research"
    )
    canvas.drawRightString(549, 30, f"{doc.page} / {TOTAL}")
    canvas.restoreState()


def build():
    base.setup_fonts()
    components = base.components()
    width = base.WIDTH
    peer = pd.read_csv(ROOT / "model_outputs/integrated/peer_comparison.csv")
    components["peers"] = base.table(
        ["Company / FY end", "Revenue", "Own FY YoY", "GAAP op. margin"],
        [
            [
                r.ticker + " / " + r.period_end,
                base.f(r.revenue),
                base.pct(r.revenue_growth),
                base.pct(r.operating_margin),
            ]
            for r in peer.itertuples()
        ],
        [180, 103, 105, width - 388],
    )
    components["peer_gates"] = base.table(
        ["Metric", "Current conclusion / missing evidence"],
        [
            [
                "EV / Revenue",
                "BLOCKED: common-date peer market EV and calendarized TTM revenue.",
            ],
            [
                "EV / EBITDA",
                "BLOCKED: EV bridge plus aligned EBIT and pure D&A definition.",
            ],
            [
                "Forward P/E",
                "BLOCKED: reliable dated NTM diluted EPS and price/period alignment.",
            ],
            [
                "Growth / operating margin",
                "Available only as own-fiscal-year historical context above.",
            ],
        ],
        [125, width - 125],
    )
    components["catalysts"] = base.table(
        ["Monitoring test", "What would weaken the thesis"],
        [
            [
                "Accepted deployments / customer mix",
                "Spending reprioritization, acceptance delays or concentration-driven volatility. [K p.7; Q pp.14–15]",
            ],
            [
                "Renewals / customer economics",
                "Weak independent evidence of software benefits; procurement bundling or rival architectures. [K pp.6–9; N p.5]",
            ],
            [
                "Matched-period margins / cash flow",
                "Persistent gross-margin pressure or deferred-cost / inventory absorption without cash conversion. [Q pp.5,9,16,18–19]",
            ],
        ],
        [173, width - 173],
    )
    names = {
        "K": "ANET 2025 10-K: business pp.1–9; statements pp.68–69,72; leases p.86.",
        "Q": "ANET Sep. 2026 10-Q: statements pp.1,2,5; notes pp.6–12; MD&A pp.14–19.",
        "N": "NVIDIA FY2026 10-K: networking p.5; consolidated income p.51.",
        "C": "Cisco FY2026 10-K: consolidated operations p.57; cash flows p.59.",
        "M": "Stock Analysis ANET history: table Close; corroborated by ChartExchange (see U).",
        "R1": "Original forecast / DCF methodology.",
        "R2": "Original valuation evidence / bridge audit.",
        "R3": "Sourced research draft; preliminary hypotheses and risks.",
        "R4": "Quarterly / TTM income methodology.",
        "U": "Integrated methodology: rechecks, ledger, dilution, peers, price/rating and reproducibility.",
    }
    components["sources"] = base.table(
        ["Reference", "Source / scope (click to open)"],
        [
            [
                k,
                Paragraph(
                    '<a href="' + URLS[k] + '" color="#147D85">' + escape(v) + "</a>",
                    base.style(7.8, 10.5),
                ),
            ]
            for k, v in names.items()
        ],
        [63, width - 63],
        size=7.8,
    )
    pages = SOURCE.read_text().split("---PAGE---")
    if len(pages) != TOTAL:
        raise ValueError("Expected ten explicit page sections.")
    story = []
    for n, page in enumerate(pages):
        if n:
            story.append(PageBreak())
        page = re.sub(r"(?m)^(#{1,3} .+)$", r"\n\1\n", page)
        for block in re.split(r"\n\s*\n", page.strip()):
            block = " ".join(block.splitlines())
            if block.startswith("{{"):
                story.extend([components[block[2:-2]], Spacer(1, 10)])
            elif block.startswith("### "):
                story.append(
                    Paragraph(
                        escape(block[4:]),
                        base.style(10.4, 14, fontName="Bold", spaceBefore=6),
                    )
                )
            elif block.startswith("## "):
                story.append(
                    Paragraph(
                        escape(block[3:]),
                        base.style(14, 19, fontName="Bold", spaceBefore=2),
                    )
                )
            elif block.startswith("# "):
                story.append(
                    Paragraph(
                        escape(block[2:]),
                        base.style(
                            19 if n == 0 else 16, 24, fontName="Bold", spaceBefore=6
                        ),
                    )
                )
            else:
                story.append(paragraph(block))
    SimpleDocTemplate(
        str(PDF),
        pagesize=(595.28, 841.89),
        leftMargin=46,
        rightMargin=46,
        topMargin=49,
        bottomMargin=47,
        title="Arista Networks (NYSE: ANET) — Equity Research & Scenario-Based DCF Valuation | Integrated v2",
        author="Ya-Cheng Hsieh (Erica Hsieh)",
        invariant=1,
    ).build(story, onFirstPage=footer, onLaterPages=footer)
    inputs = (
        [ROOT / p for p in base.INPUTS]
        + [SOURCE, Path(__file__).resolve()]
        + list((ROOT / "data/integrated").glob("*.json"))
        + list((ROOT / "model_outputs/integrated").glob("*"))
        + [
            ROOT / "docs/integrated_valuation_methodology.md",
            ROOT / "docs/peer_valuation.md",
            ROOT / "docs/price_target_framework.md",
            ROOT / "docs/investment_framework.md",
        ]
    )
    manifest = {
        "research_date": "2026-11-08",
        "timezone": "America/New_York",
        "main_baseline": "6c1498f",
        "page_count": TOTAL,
        "pdf": str(PDF.relative_to(ROOT)),
        "input_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(set(inputs))
        },
        "pdf_sha256": hashlib.sha256(PDF.read_bytes()).hexdigest(),
        "status": "NOT RATED; target/equity/per-share BLOCKED; scenarios HYPOTHETICAL / NOT YET VALIDATED",
    }
    (ROOT / "reports/integrated_report_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    print(PDF)


if __name__ == "__main__":
    build()
