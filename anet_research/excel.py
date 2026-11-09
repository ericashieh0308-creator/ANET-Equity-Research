"""Read the supplied historical model without writing or executing Excel formulas.

Only this documented worksheet layout and formula set is supported. Values are
recomputed from literal inputs; cached Excel results are used solely for audit.
"""

from io import BytesIO
from math import isclose, isfinite
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from anet_research.financials import REQUIRED_COLUMNS, calculate_metrics

WORKBOOK = Path(__file__).resolve().parents[1] / "data/source/ANET_Financial Model.xlsx"
LABELS = {
    2: "Product Revenue", 3: "Service Revenue", 4: "Total Revenue",
    5: "Revenue Growth", 6: "Cost of Revenue", 7: "Gross Profit",
    8: "Gross Margin", 9: "Operating Expenses", 10: "Operating Income",
    11: "Operating Margins", 12: "Net Income", 13: "Net Profit Margin",
}


def load_historical_workbook(source=WORKBOOK):
    """Return unverified metrics and a cell-level formula/cache audit.

    Missing literals propagate. Unexpected formulas/layouts fail explicitly.
    This does not authenticate figures or check SEC filings.
    """
    payload = Path(source).read_bytes() if isinstance(source, (str, Path)) else source.read()
    formulas = load_workbook(BytesIO(payload), data_only=False)
    cached = load_workbook(BytesIO(payload), data_only=True)
    name = "Historical Financials"
    if name not in formulas.sheetnames:
        raise ValueError("Workbook requires the Historical Financials worksheet.")
    sheet, values = formulas[name], cached[name]
    if sheet["A1"].value != "Metric (USD millions)" or any(sheet.cell(r, 1).value != label for r, label in LABELS.items()):
        raise ValueError("Unsupported historical layout or units; expected USD millions and original row labels.")
    records, audit = [], []
    for col in range(2, sheet.max_column + 1):
        year = sheet.cell(1, col).value
        if year is None:
            continue
        letter = get_column_letter(col)
        prior = get_column_letter(col - 1)
        def literal(row):
            value = sheet.cell(row, col).value
            if value is None:
                return float("nan")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
                raise ValueError(f"Expected finite literal number or blank at {letter}{row}.")
            return float(value)
        product, service, cost, expenses, net = [literal(r) for r in (2, 3, 6, 9, 12)]
        revenue = product + service
        gross = revenue - cost
        operating = gross - expenses
        records.append(dict(zip(REQUIRED_COLUMNS, [
            year, revenue, gross, operating, net, None, None, "",
            f"Uploaded workbook | {name}!{letter}2:{letter}13 | UNVERIFIED; no SEC citation", False,
        ])))
        expected = {4: f"={letter}2+{letter}3", 7: f"={letter}4-{letter}6",
                    8: f"={letter}7/{letter}4", 10: f"={letter}7-{letter}9",
                    11: f"={letter}10/{letter}4", 13: f"={letter}12/{letter}4"}
        if col > 2:
            expected[5] = f"={letter}4/{prior}4-1"
        elif sheet.cell(5, col).value is not None:
            raise ValueError("First historical year must have blank revenue growth.")
        for row, expression in expected.items():
            actual = sheet.cell(row, col).value
            if not isinstance(actual, str) or actual.replace("=+", "=").replace(" ", "") != expression:
                raise ValueError(f"Unexpected formula at {letter}{row}: expected {expression}.")
    metrics = calculate_metrics(pd.DataFrame(records, columns=REQUIRED_COLUMNS), allow_unverified=True)
    mapping = {4: "revenue", 5: "revenue_growth_yoy", 7: "gross_profit", 8: "gross_profit_margin",
               10: "operating_income", 11: "operating_profit_margin", 13: "net_profit_margin"}
    for col in range(2, sheet.max_column + 1):
        year = sheet.cell(1, col).value
        if year is None:
            continue
        record = metrics.loc[metrics.fiscal_year.eq(year)].iloc[0]
        for row, field in mapping.items():
            cell = sheet.cell(row, col)
            if cell.value is None:
                continue
            cache = values.cell(row, col).value
            computed = record[field]
            comparable = isinstance(cache, (int, float)) and not isinstance(cache, bool) and pd.notna(computed)
            status = "MATCH" if comparable and isclose(cache, computed, rel_tol=1e-9, abs_tol=1e-8) else "MISMATCH" if comparable else "NOT COMPARABLE"
            audit.append({"worksheet": name, "cell": cell.coordinate, "fiscal_year": year,
                          "metric": field, "formula": cell.value, "excel_cached": cache,
                          "python_calculated": computed, "status": status})
    metrics["verification_status"] = "UNVERIFIED — uploaded workbook; not SEC checked"
    return metrics, pd.DataFrame(audit)
