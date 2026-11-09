"""Streamlit entry point: streamlit run app.py."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from anet_research.financials import FINANCIAL_FIELDS, calculate_metrics
from anet_research.excel import WORKBOOK, load_historical_workbook
from anet_research.sec import FCF_LABEL, load_verified_metrics, reconciliation
from anet_research.interim import VIEW
from anet_research.interim_view import render_interim

TEMPLATE = Path(__file__).parent / "data" / "annual_financials_template.csv"
RATIOS = ["revenue_growth_yoy", "gross_profit_margin", "operating_profit_margin",
          "net_profit_margin", "free_cash_flow_margin"]

st.set_page_config(page_title="ANET | Financial Research", page_icon="📊", layout="wide")
st.title("ANET · Financial Research")
st.caption("Arista Networks | Financial statements | USD millions unless noted")
with st.sidebar:
    st.header("Financial statements")
    source_mode = st.radio("Data source", ["Existing Excel model (unverified)", "Verified CSV", "Verified local 2025 Form 10-K", VIEW])
    st.download_button("Download blank CSV template", TEMPLATE.read_bytes(),
                       "annual_financials_template.csv", "text/csv")
    uploaded = st.file_uploader("Upload verified annual data", type=["csv"]) if source_mode == "Verified CSV" else None
    st.caption("CSV imports use USD millions and capex as a positive outflow, with an SEC URL and filing page/table reference. Source statement exports retain reported signs.")

if source_mode == VIEW:
    render_interim()
    st.stop()

st.info("Workbook figures and derived ratios are UNVERIFIED until checked against SEC 10-K filings. CSV verification is a user attestation. No investment recommendations are generated.")

try:
    audit = None
    if source_mode == "Existing Excel model (unverified)":
        metrics, audit = load_historical_workbook()
        st.warning("UNVERIFIED workbook figures and calculated ratios · USD millions · SEC sources absent. Operating cash flow and capex are missing; FCF remains blank.")
        with st.expander("Excel formula reconciliation & provenance"):
            st.caption(f"Source: {WORKBOOK.name} / Historical Financials. Recomputed from literal inputs; original workbook is read only. A formula match does not verify the financial figures.")
            st.dataframe(audit, hide_index=True, width="stretch")
            if audit["status"].ne("MATCH").any():
                st.warning("Some Excel cached results differ or cannot be compared; review the audit before use.")
        with st.expander("Original historical worksheet — UNVERIFIED cached values"):
            st.caption("Includes product/service revenue, cost of revenue and operating expenses. These are the workbook's saved values; the analysis above recomputes supported formulas independently.")
            original = pd.read_excel(WORKBOOK, sheet_name="Historical Financials", engine="openpyxl")
            original.columns = original.columns.map(str)
            st.dataframe(original, hide_index=True, width="stretch")
    elif source_mode == "Verified local 2025 Form 10-K":
        metrics = load_verified_metrics()
        st.success("2023–2025 figures checked against local PDF pages 73 and 76; no outside authentication performed.")
        st.warning("2023 balance sheet unavailable in this PDF. 2024–2025 balance sheets are present but not reconciled here. PP&E-only cash purchases are not separately disclosed.")
        st.caption(FCF_LABEL + " = operating cash flow − absolute value of purchases of property, equipment and intangible assets. This is not PP&E-only FCF.")
        with st.expander("Excel versus local Form 10-K reconciliation"):
            comparison = reconciliation()
            st.dataframe(comparison, hide_index=True, width="stretch")
            st.download_button("Download reconciliation CSV", comparison.to_csv(index=False), "anet_reconciliation.csv", "text/csv")
            if comparison.status.eq("DISCREPANCY").any():
                st.warning("Discrepancies found; review reconciliation rows.")
            st.caption("Missing Excel cash-flow inputs are not filled in the workbook. 2023 revenue growth is unavailable because 2022 revenue is absent. Differences = Excel − SEC; ratios are derived from SEC amounts.")
    else:
        statements = pd.read_csv(uploaded if uploaded is not None else TEMPLATE)
        metrics = calculate_metrics(statements)
        metrics["verification_status"] = "User-attested CSV; not independently SEC checked"
except (ValueError, OSError, pd.errors.ParserError, UnicodeError) as exc:
    st.error(f"Cannot analyze this file: {exc}")
    st.stop()

if metrics.empty or not metrics[FINANCIAL_FIELDS].notna().any().any():
    st.warning("No verified financial figures loaded. Download the template, fill it from SEC 10-K filings, and upload it to begin.")
    st.dataframe(metrics, hide_index=True, width="stretch")
else:
    years = metrics["fiscal_year"].tolist()
    selected = st.sidebar.multiselect("Fiscal years", years, default=years)
    shown = metrics[metrics["fiscal_year"].isin(selected)]
    st.caption("YoY is calculated using the complete uploaded history before the display filter. Missing inputs and undefined ratios remain blank.")
    if shown.empty:
        st.warning("Select at least one fiscal year.")
    else:
        if source_mode == "Existing Excel model (unverified)":
            st.subheader("Historical analysis — UNVERIFIED")
        verified_pdf = source_mode == "Verified local 2025 Form 10-K"
        display_names = {"free_cash_flow": FCF_LABEL,
                         "free_cash_flow_margin": FCF_LABEL + " margin",
                         "capital_expenditures": "Absolute property, equipment and intangible purchases"} if verified_pdf else {}
        latest = shown.iloc[-1]
        cols = st.columns(3)
        for col, field, title, percent in [
            (cols[0], "revenue", "Revenue (USD m)", False),
            (cols[1], "revenue_growth_yoy", "Revenue YoY", True),
            (cols[2], "free_cash_flow", (FCF_LABEL if verified_pdf else "Free cash flow") + " (USD m)", False),
        ]:
            value = latest[field]
            col.metric(f"{title} · {int(latest['fiscal_year'])}",
                       "N/A" if pd.isna(value) else (f"{value:.1%}" if percent else f"{value:,.2f}"))
        amounts_tab, margins_tab, table_tab = st.tabs(["Financial performance", "Growth & margins", "Data & sources"])
        with amounts_tab:
            amounts = st.multiselect("Financial series", FINANCIAL_FIELDS + ["free_cash_flow"],
                                    default=["revenue", "free_cash_flow"],
                                    format_func=lambda field: display_names.get(field, field))
            if amounts:
                fig = px.bar(shown.rename(columns=display_names), x="fiscal_year", y=[display_names.get(field, field) for field in amounts], barmode="group",
                             labels={"value": "USD millions", "fiscal_year": "Fiscal year"})
                fig.update_xaxes(type="category")
                st.plotly_chart(fig, width="stretch")
        with margins_tab:
            fig = px.line(shown.rename(columns=display_names), x="fiscal_year", y=[display_names.get(field, field) for field in RATIOS], markers=True,
                          labels={"value": "Ratio", "fiscal_year": "Fiscal year"})
            fig.update_yaxes(tickformat=".0%")
            fig.update_xaxes(type="category")
            st.plotly_chart(fig, width="stretch")
        with table_tab:
            st.dataframe(shown.rename(columns=display_names).style.format({display_names.get(key, key): "{:.2%}" for key in RATIOS}, na_rep="—"),
                         hide_index=True, width="stretch")
            st.download_button("Download analysis CSV", shown.rename(columns=display_names).to_csv(index=False),
                               "anet_financial_analysis.csv", "text/csv")

with st.expander("Methodology & data conventions"):
    st.markdown("""
    - Revenue YoY = current revenue / prior fiscal year revenue − 1.
      Requires consecutive fiscal years and positive prior revenue.
    - Gross, operating and net margins = respective profit / revenue.
    - Free cash flow = operating cash flow − capital expenditures (positive outflow).
    - In the verified local PDF view, FCF after property, equipment and intangible purchases
      = operating cash flow − absolute value of that combined purchase line (PDF p.76).
      This includes intangible assets and is not traditional PP&E-only FCF.
    - Free cash flow margin = free cash flow / revenue.
    - Ratios with zero or missing revenue remain blank. Missing inputs are never filled.
    - Use consolidated annual figures, consistent USD millions, and consistent restatements.
      FCF is a derived non-GAAP measure; its definition may differ from company disclosures.
    """)
