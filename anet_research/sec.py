"""Locally transcribed 2025 10-K data; no network access or workbook writes."""
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

from anet_research.financials import calculate_metrics

ROOT = Path(__file__).resolve().parents[1]
FCF_LABEL = "FCF after property, equipment and intangible purchases"


def load_verified_metrics():
    data = pd.read_csv(ROOT / "data/verified_2023_2025.csv")
    # Retain the signed statement line; the generic calculation expects positive outflow.
    data["capital_expenditures"] = data["property_equipment_intangible_purchases"].abs()
    result = calculate_metrics(data)
    for column in data.columns.difference(result.columns):
        result[column] = data[column].to_numpy()
    result["verification_status"] = "Checked against local 2025 Form 10-K; not externally authenticated"
    result["fcf_definition"] = FCF_LABEL
    result["balance_sheet_status"] = result.fiscal_year.map({
        2023: "Unavailable in this PDF", 2024: "Present on PDF p.72; not reconciled here",
        2025: "Present on PDF p.72; not reconciled here"})
    return result


def reconciliation():
    """Compare original cached Excel figures with reported or SEC-derived figures."""
    data = load_verified_metrics()
    sheet = load_workbook(ROOT / "ANET_Financial Model.xlsx", data_only=True)["Historical Financials"]
    fields = {2: "product_revenue", 3: "service_revenue", 4: "revenue", 5: "revenue_growth_yoy",
              6: "cost_of_revenue", 7: "gross_profit", 8: "gross_profit_margin",
              9: "operating_expenses", 10: "operating_income", 11: "operating_profit_margin",
              12: "net_income", 13: "net_profit_margin"}
    rows = []
    for col in range(2, 5):
        year = sheet.cell(1, col).value
        sec = data.loc[data.fiscal_year.eq(year)].iloc[0]
        for row, field in fields.items():
            excel, value = sheet.cell(row, col).value, sec[field]
            derived = field.endswith("margin") or field == "revenue_growth_yoy"
            missing = excel is None or pd.isna(value)
            difference = None if missing else excel - value
            rows.append(dict(fiscal_year=year, metric=field, excel_cell=f"Historical Financials!{sheet.cell(row,col).coordinate}",
                             excel_value=excel, sec_value=value, difference=difference,
                             units="fraction" if derived else "USD millions",
                             status="MISSING / NOT COMPARABLE" if missing else "MATCH" if abs(difference) < 1e-8 else "DISCREPANCY",
                             pdf_reference="PDF p.73 (printed p.69)",
                             basis="Derived from SEC amounts" if derived else "Reported SEC amount"))
        for field in ["operating_cash_flow", "property_equipment_intangible_purchases", "free_cash_flow", "free_cash_flow_margin"]:
            rows.append(dict(fiscal_year=year, metric=field, excel_cell="Not present", excel_value=None,
                             sec_value=sec[field], difference=None, units="fraction" if field.endswith("margin") else "USD millions",
                             status="MISSING IN EXCEL", pdf_reference="PDF p.76 (printed p.72)" + ("; p.73 revenue" if field.endswith("margin") else ""),
                             basis="Derived: " + FCF_LABEL if field.startswith("free_cash_flow") else "Reported SEC amount"))
    return pd.DataFrame(rows)
