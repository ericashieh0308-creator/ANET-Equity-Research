"""TTM arithmetic, verification gates and separate interim dashboard regression."""
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from anet_research.interim import (
    ROOT, VIEW, DISPLAY_FIELDS, load_interim, load_ttm_annual, comparisons, ttm_income, yoy,
)


def inputs():
    interim,_ = load_interim()
    return load_ttm_annual(),interim


def test_actual_ttm_amounts_and_provenance():
    annual,interim=inputs()
    result=ttm_income(annual,interim).set_index('metric')
    expected={'revenue':11890.1,'cost_of_revenue':4413.5,'gross_profit':7476.6,
              'operating_expenses':2265.5,'operating_income':5211.1,'net_income':4752.0}
    for field,value in expected.items():
        row=result.loc[field]
        assert row.value==pytest.approx(value)
        assert row.value==pytest.approx(row.fy2025+row.nine_months_2026-row.nine_months_2025)
        assert row.status=='VERIFIED INPUTS; analytical TTM'
        assert 'p.73' in row.annual_source_reference and 'p.2' in row.interim_source_reference
        assert 'October 1, 2025' in row.period
    assert result.loc['gross_profit','value']-result.loc['operating_expenses','value']==pytest.approx(result.loc['operating_income','value'])
    assert pd.isna(result.loc['diluted_eps','value'])
    assert 'weighted-average' in result.loc['diluted_eps','status']
    assert pd.isna(result.loc['free_cash_flow','value'])
    assert 'intangibles' in result.loc['free_cash_flow','status']


def test_ttm_is_general_arithmetic_not_fixed_answer():
    annual,interim=inputs()
    annual.loc[annual.fiscal_year.eq(2025),'revenue']=1000
    interim.loc[interim.period.eq('9M 2026'),'revenue']=800
    interim.loc[interim.period.eq('9M 2025'),'revenue']=600
    assert ttm_income(annual,interim).set_index('metric').loc['revenue','value']==1200


@pytest.mark.parametrize('target', ['annual','current','prior'])
def test_missing_input_does_not_fill_or_contaminate_other_metrics(target):
    annual,interim=inputs()
    if target=='annual':
        annual.loc[annual.fiscal_year.eq(2025),'revenue']=None
    else:
        interim.loc[interim.period.eq('9M 2026' if target=='current' else '9M 2025'),'revenue']=None
    result=ttm_income(annual,interim).set_index('metric')
    assert pd.isna(result.loc['revenue','value'])
    assert 'UNAVAILABLE' in result.loc['revenue','status']
    assert result.loc['net_income','value']==pytest.approx(4752)


@pytest.mark.parametrize('target,field,value', [
    ('annual','verified',False),('current','verified','false'),('prior','source_url','https://example.com'),
    ('current','duration_months',3),('prior','period_start','2025-07-01'),
    ('current','units','USD thousands'),('annual','income_units','USD thousands'),
    ('annual','source_reference',None),
])
def test_ttm_blocks_unverified_or_incompatible_periods_and_units(target,field,value):
    annual,interim=inputs()
    frame=annual if target=='annual' else interim
    mask=annual.fiscal_year.eq(2025) if target=='annual' else interim.period.eq('9M 2026' if target=='current' else '9M 2025')
    frame[field]=frame[field].astype(object)
    frame.loc[mask,field]=value
    result=ttm_income(annual,interim)
    assert result.value.isna().all()


@pytest.mark.parametrize('target',['annual','current','prior','duplicate'])
def test_ttm_missing_or_duplicate_period_is_unavailable(target):
    annual,interim=inputs()
    if target=='annual':annual=annual[annual.fiscal_year.ne(2025)]
    elif target=='duplicate':interim=pd.concat([interim,interim[interim.period.eq('9M 2026')]])
    else:interim=interim[interim.period.ne('9M 2026' if target=='current' else '9M 2025')]
    assert ttm_income(annual,interim).value.isna().all()


def test_like_period_growth_and_eps_rounding_label():
    _,interim=inputs()
    c=comparisons(interim)
    assert len(c)==10
    assert set(c.period_type)=={'Quarter (Q3)','Nine months YTD (9M)'}
    assert set(c.metric)==set(DISPLAY_FIELDS)
    revenue=c[c.metric.eq('revenue')]
    assert revenue.iloc[0].yoy_growth==pytest.approx(3657.6/2308.3-1)
    assert revenue.iloc[1].yoy_growth==pytest.approx(9402.3/6517.9-1)
    assert c[c.metric.eq('diluted_eps')].growth_note.eq('Based on rounded reported EPS').all()
    for a,b in [(None,1),(1,None),(1,0),(1,-1)]:assert yoy(a,b) is None
    interim.loc[interim.period.eq('Q3 2025'),'duration_months']=9
    with pytest.raises(ValueError,match='duration'):comparisons(interim)


def test_quarterly_source_tampering_is_rejected(monkeypatch):
    import anet_research.interim as module
    real_read=module._read
    def tampered(path):
        rows=real_read(path)
        if path.name.endswith('_metrics.csv'):rows[0]['revenue']='1'
        return rows
    monkeypatch.setattr(module,'_read',tampered)
    with pytest.raises(ValueError,match='metrics differ'):module.load_interim()


def test_interim_dashboard_labels_exports_and_mode_switching():
    app=AppTest.from_file(str(ROOT/'app.py')).run()
    app.sidebar.radio[0].set_value(VIEW).run()
    assert not app.exception
    assert [tab.label for tab in app.tabs]==['Q3: three months ended September 30','9M: nine months ended September 30']
    assert len(app.get('plotly_chart'))==2
    assert any('nine-month YTD' in w.value for w in app.warning)
    assert any('TTM FCF not calculated' in w.value for w in app.warning)
    assert any('not additive' in i.value for i in app.info)
    labels=[b.label for b in app.get('download_button')]
    assert 'Download TTM income analysis CSV' in labels
    assert 'Download 9M cash flow analysis CSV' in labels
    # First two tables are quarterly and nine-month comparisons; TTM is separate.
    assert set(app.dataframe[0].value.current_period)=={'Three Months Ended September 30, 2026'}
    assert set(app.dataframe[1].value.current_period)=={'Nine Months Ended September 30, 2026'}
    cash=app.dataframe[2].value
    assert cash.duration_months.eq(9).all()
    assert set(cash.period_label)=={'Nine Months Ended September 30, 2026','Nine Months Ended September 30, 2025'}
    assert cash.operating_cash_flow.iloc[0]==3977.4
    assert pd.isna(cash.operating_cash_flow_yoy.iloc[1])
    ttm=app.dataframe[3].value.set_index('metric')
    assert ttm.loc['Revenue','value']==pytest.approx(11890.1)
    assert pd.isna(ttm.loc['Diluted EPS','value'])
    assert pd.isna(ttm.loc['TTM FCF (blocked)','value'])
    app.sidebar.radio[0].set_value('Verified local 2025 Form 10-K').run()
    assert not app.exception and app.metric[2].value=='4,252.40'
    app.sidebar.radio[0].set_value('Existing Excel model (unverified)').run()
    assert not app.exception and app.metric[2].value=='N/A'
