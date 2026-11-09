"""Regression checks against the locally reviewed PDF, not synthetic source data."""
import hashlib
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from anet_research.sec import ROOT, FCF_LABEL, load_verified_metrics, reconciliation


@pytest.mark.parametrize('year,revenue,ocf,purchases,fcf', [
    (2023, 5860.2, 2034.0, -34.4, 1999.6),
    (2024, 7003.1, 3708.2, -32.0, 3676.2),
    (2025, 9005.7, 4371.9, -119.5, 4252.4),
])
def test_verified_fcf_and_provenance(year, revenue, ocf, purchases, fcf):
    row = load_verified_metrics().set_index('fiscal_year').loc[year]
    assert row.revenue == revenue
    assert row.operating_cash_flow == ocf
    assert row.property_equipment_intangible_purchases == purchases
    assert row.capital_expenditures == abs(purchases)
    assert row.free_cash_flow == pytest.approx(fcf)
    assert row.free_cash_flow_margin == pytest.approx(fcf / revenue)
    assert row.fcf_definition == FCF_LABEL
    assert 'p.73' in row.source_reference and 'p.76' in row.source_reference


def test_reconciliation_and_workbooks_preserved():
    paths = [ROOT / 'ANET_Financial Model.xlsx', ROOT / 'data/source/ANET_Financial Model.xlsx']
    before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
    r = reconciliation()
    assert len(r) == 48
    assert r.status.value_counts().to_dict() == {'MATCH': 35, 'MISSING IN EXCEL': 12, 'MISSING / NOT COMPARABLE': 1}
    missing = r[r.status.ne('MATCH')]
    assert missing.excel_value.isna().all() and missing.difference.isna().all()
    growth = r[(r.fiscal_year == 2023) & (r.metric == 'revenue_growth_yoy')].iloc[0]
    assert pd.isna(growth.sec_value)
    assert load_verified_metrics().iloc[0].balance_sheet_status == 'Unavailable in this PDF'
    assert before == [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
    assert set(before) == {'571b693f69a6644c5cab649b169f191ab404f69c90c8d55e733dd827c07ad5b3'}


def test_verified_dashboard_filter_and_definition():
    app = AppTest.from_file(str(ROOT / 'app.py')).run()
    app.sidebar.radio[0].set_value('Verified local 2025 Form 10-K').run()
    assert not app.exception
    assert app.metric[2].value == '4,252.40'
    assert FCF_LABEL in app.metric[2].label
    assert '2023 balance sheet unavailable' in app.warning[0].value
    assert len(app.get('plotly_chart')) == 2
    app.sidebar.multiselect[0].set_value([2024]).run()
    assert not app.exception
    assert app.metric[2].value == '3,676.20'
    assert app.metric[1].value == '19.5%'


@pytest.mark.parametrize('signed_purchase', [-34.4, 34.4, None])
def test_absolute_purchase_and_missing_propagation(monkeypatch, signed_purchase):
    data = pd.read_csv(ROOT / 'data/verified_2023_2025.csv')
    data.loc[0, 'property_equipment_intangible_purchases'] = signed_purchase
    monkeypatch.setattr(pd, 'read_csv', lambda *args, **kwargs: data.copy())
    row = load_verified_metrics().iloc[0]
    if signed_purchase is None:
        assert pd.isna(row.free_cash_flow) and pd.isna(row.free_cash_flow_margin)
    else:
        assert row.free_cash_flow == pytest.approx(1999.6)


def test_reconciliation_flags_a_changed_excel_amount(monkeypatch):
    import anet_research.sec as sec
    from openpyxl import load_workbook
    workbook = load_workbook(ROOT / 'ANET_Financial Model.xlsx', data_only=True)
    workbook['Historical Financials']['B12'] = 2000
    monkeypatch.setattr(sec, 'load_workbook', lambda *args, **kwargs: workbook)
    row = sec.reconciliation().query("fiscal_year == 2023 and metric == 'net_income'").iloc[0]
    assert row.status == 'DISCREPANCY'
    assert row.difference == pytest.approx(-87.3)
