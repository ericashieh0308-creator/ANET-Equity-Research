"""Synthetic arithmetic fixtures only; these are not ANET financial figures."""

import pandas as pd
import pytest

from anet_research.financials import REQUIRED_COLUMNS, calculate_metrics


def fixture():
    return pd.DataFrame([
        [2022, 100, 60, 30, 20, 25, 5, "https://www.sec.gov/example", "Synthetic test only", True],
        [2023, 120, 72, 36, 24, 35, 5, "https://www.sec.gov/example", "Synthetic test only", True],
    ], columns=REQUIRED_COLUMNS)


def test_formulas_and_sorting():
    result = calculate_metrics(fixture().iloc[::-1])
    assert result.fiscal_year.tolist() == [2022, 2023]
    row = result.iloc[1]
    assert row.revenue_growth_yoy == pytest.approx(.2)
    assert row.gross_profit_margin == pytest.approx(.6)
    assert row.operating_profit_margin == pytest.approx(.3)
    assert row.net_profit_margin == pytest.approx(.2)
    assert row.free_cash_flow == 30
    assert row.free_cash_flow_margin == pytest.approx(.25)
    assert pd.isna(result.iloc[0].revenue_growth_yoy)


def test_gaps_missing_and_zero_denominators():
    data = fixture()
    data.loc[0, "revenue"] = 0
    data.loc[1, "capital_expenditures"] = None
    result = calculate_metrics(data)
    assert pd.isna(result.iloc[0].gross_profit_margin)
    assert pd.isna(result.iloc[1].revenue_growth_yoy)
    assert pd.isna(result.iloc[1].free_cash_flow)
    data.loc[0, "revenue"] = 100
    data.loc[1, "fiscal_year"] = 2024
    assert pd.isna(calculate_metrics(data).iloc[1].revenue_growth_yoy)


@pytest.mark.parametrize("field,value", [
    ("fiscal_year", 2022), ("revenue", "bad"), ("revenue", float("inf")),
    ("capital_expenditures", -1), ("verified", False),
    ("source_url", "https://sec.gov.evil.example/filing"), ("source_reference", ""),
])
def test_invalid_input_rejected(field, value):
    data = fixture()
    data[field] = data[field].astype(object)
    data.loc[1, field] = value
    with pytest.raises(ValueError):
        calculate_metrics(data)


def test_blank_template_and_missing_columns():
    from pathlib import Path
    template = Path(__file__).resolve().parents[1] / "data/annual_financials_template.csv"
    assert calculate_metrics(pd.read_csv(template)).empty
    with pytest.raises(ValueError, match="Missing columns"):
        calculate_metrics(pd.DataFrame())


def test_blank_financial_row_stays_missing():
    row = pd.DataFrame([[2024, *([None] * 9)]], columns=REQUIRED_COLUMNS)
    result = calculate_metrics(row)
    assert pd.isna(result.iloc[0].free_cash_flow)
    assert pd.isna(result.iloc[0].net_profit_margin)
