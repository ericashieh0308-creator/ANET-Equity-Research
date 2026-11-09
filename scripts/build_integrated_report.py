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
from reportlab.graphics.shapes import Drawing, Rect, String, Line

SOURCE = ROOT / "reports/anet_integrated_research.md"
PDF = ROOT / "reports/ANET_Integrated_Equity_Research_v2.pdf"
TOTAL = 10
URLS = dict(base.URLS)
URLS.update(
    C="https://www.sec.gov/Archives/edgar/data/858877/000085887726000132/csco-20260725.htm",
    M="https://stockanalysis.com/stocks/anet/history/",
    U="https://github.com/ericashieh0308-creator/ANET-Equity-Research/blob/334d975cf2412a4211fc7c84fe479b6a31efc7ae/docs/integrated_valuation_methodology.md",
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


def financial_highlight_rows():
    """Presentation-only, matched-period calculations from preserved interim data."""
    q = pd.read_csv(ROOT / "data/quarterly/anet_20260930_metrics.csv").set_index(
        "period"
    )
    current, prior = q.loc["9M 2026"], q.loc["9M 2025"]
    rows = []
    for label, key in [
        ("Revenue", "revenue"),
        ("Operating income", "operating_income"),
    ]:
        rows.append(
            [
                label,
                base.f(current[key]),
                f"+{(current[key] / prior[key] - 1) * 100:.1f}%",
            ]
        )
    for label, key in [
        ("Gross margin", "gross_profit"),
        ("Operating margin", "operating_income"),
    ]:
        margin = current[key] / current.revenue
        change = 100 * (margin - prior[key] / prior.revenue)
        rows.append([label, base.pct(margin), f"{change:+.1f} pp"])
    rows.append(
        [
            "Operating cash flow (OCF)",
            base.f(current.operating_cash_flow),
            f"+{(current.operating_cash_flow / prior.operating_cash_flow - 1) * 100:.1f}%",
        ]
    )
    return rows


def labeled_bars(
    labels, values, title, maximum, width=base.WIDTH, height=150, percent=False
):
    """Zero-based vector bars with direct labels and round-number gridlines."""
    drawing = Drawing(width, height)
    drawing.add(
        String(
            0, height - 11, title, fontName="Bold", fontSize=8.5, fillColor=base.NAVY
        )
    )
    left, bottom, top = 38, 27, height - 35
    plot_width = width - left - 8
    for fraction in [0, 0.5, 1]:
        y = bottom + (top - bottom) * fraction
        drawing.add(
            Line(
                left,
                y,
                left + plot_width,
                y,
                strokeColor=base.colors.HexColor("#DDE5EA"),
                strokeWidth=0.4,
            )
        )
        value = maximum * fraction
        label = f"{value:g}%" if percent else f"{value:,.0f}"
        drawing.add(
            String(
                left - 5,
                y - 3,
                label,
                fontName="Body",
                fontSize=7.1,
                textAnchor="end",
                fillColor=base.GRAY,
            )
        )
    for i, (label, value) in enumerate(zip(labels, values)):
        x = left + plot_width * (i + 0.5) / len(values)
        h = (top - bottom) * value / maximum
        drawing.add(Rect(x - 10, bottom, 20, h, fillColor=base.TEAL, strokeColor=None))
        value_label = f"{value:.1f}%" if percent else base.f(value)
        drawing.add(
            String(
                x,
                bottom + h + 5,
                value_label,
                fontName="Bold",
                fontSize=7.5,
                textAnchor="middle",
                fillColor=base.NAVY,
            )
        )
        drawing.add(
            String(
                x,
                bottom - 13,
                label,
                fontName="Body",
                fontSize=7.5,
                textAnchor="middle",
                fillColor=base.NAVY,
            )
        )
    return drawing


def editorial_charts():
    annual = pd.read_csv(ROOT / "data/verified_2023_2025.csv")
    q = pd.read_csv(ROOT / "data/quarterly/anet_20260930_metrics.csv").set_index(
        "period"
    )
    labels = [f"FY{int(year)}" for year in annual.fiscal_year]
    combined = Drawing(base.WIDTH, 150)
    revenue = labeled_bars(
        labels,
        annual.revenue.tolist(),
        "Reported revenue | USD millions",
        10000,
        width=278,
    )
    margins = labeled_bars(
        labels,
        (100 * annual.operating_income / annual.revenue).tolist(),
        "Derived operating margin | %",
        50,
        width=210,
        percent=True,
    )
    combined.add(revenue)
    margins.translate(293, 0)
    combined.add(margins)
    current, prior = q.loc["9M 2026"], q.loc["9M 2025"]
    cash = labeled_bars(
        ["Revenue", "Operating cash flow", "PP&E-only FCF"],
        [
            100 * (current[key] / prior[key] - 1)
            for key in ["revenue", "operating_cash_flow", "analytical_fcf_ppe_only"]
        ],
        "9M2026 YoY growth | analyst-derived, %",
        50,
        percent=True,
    )
    return combined, cash


def build():
    base.setup_fonts()
    components = base.components()
    width = base.WIDTH
    components["highlights"] = base.table(
        ["Metric", "9M2026", "YoY change"],
        financial_highlight_rows(),
        [220, 130, width - 350],
    )
    components["annual_chart"], components["cash_chart"] = editorial_charts()
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
        ["Metric", "Status / evidence needed"],
        [
            [
                "EV / Revenue",
                "Unavailable: common-date peer market EV and calendarized TTM revenue required.",
            ],
            [
                "EV / EBITDA",
                "Unavailable: EV bridge plus aligned EBIT and pure D&A definition required.",
            ],
            [
                "Forward P/E",
                "Unavailable: reliable dated NTM diluted EPS and price/period alignment required.",
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
