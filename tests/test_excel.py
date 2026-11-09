from io import BytesIO
import hashlib

import pandas as pd
import pytest
from openpyxl import load_workbook
from streamlit.testing.v1 import AppTest

from anet_research.excel import WORKBOOK, load_historical_workbook
from anet_research.financials import calculate_metrics


def test_workbook_reconciles_and_is_unchanged():
    before = hashlib.sha256(WORKBOOK.read_bytes()).hexdigest()
    metrics, audit = load_historical_workbook()
    assert metrics.fiscal_year.tolist() == [2023, 2024, 2025]
    assert len(audit) == 20
    assert audit.status.eq("MATCH").all()
    assert not metrics.verified.any()
    assert metrics[["operating_cash_flow", "capital_expenditures", "free_cash_flow", "free_cash_flow_margin"]].isna().all().all()
    assert metrics.iloc[0].revenue == pytest.approx(5860.2)
    assert pd.isna(metrics.iloc[0].revenue_growth_yoy)
    assert metrics.source_url.eq("").all()
    with pytest.raises(ValueError, match="Populated rows"):
        calculate_metrics(metrics)
    assert hashlib.sha256(WORKBOOK.read_bytes()).hexdigest() == before


def altered_workbook(cell, value):
    wb = load_workbook(WORKBOOK)
    wb["Historical Financials"][cell] = value
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return stream


def test_unexpected_formula_rejected():
    with pytest.raises(ValueError, match="Unexpected formula"):
        load_historical_workbook(altered_workbook("B4", "=B2-B3"))


def test_missing_input_is_not_invented():
    metrics, audit = load_historical_workbook(altered_workbook("B2", None))
    assert pd.isna(metrics.iloc[0].revenue)
    assert pd.isna(metrics.iloc[1].revenue_growth_yoy)
    assert audit.status.eq("NOT COMPARABLE").all()


def test_default_workbook_dashboard():
    app = AppTest.from_file(str(WORKBOOK.parents[2] / "app.py")).run()
    assert not app.exception
    assert "UNVERIFIED" in app.warning[0].value
    assert len(app.metric) == 3
    assert app.metric[2].value == "N/A"
    assert len(app.get("plotly_chart")) == 2
