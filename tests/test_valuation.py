"""FCFF/DCF arithmetic and explicit gating; examples are not financial recommendations."""
import copy
import hashlib
import json
import math

import pandas as pd
import pytest

from anet_research.valuation import (
    ASSUMPTIONS, BRIDGE, ROOT, STATUS, load_inputs, forecast, dcf,
    equity_bridge, sensitivity, validate_scenario, operating_nwc, build,
)


def settings():
    config=json.loads(ASSUMPTIONS.read_text())
    return config['scenarios']['Base'],json.loads(BRIDGE.read_text())


def test_source_inputs_and_partial_year_arithmetic():
    i=load_inputs();s,b=settings();f=forecast(i,s,'Base')
    assert i['q4_2025_revenue']==pytest.approx(2487.8)
    assert i['ytd_da']==70.3 and i['ytd_ppe_capex']==184.9
    assert i['opening_nwc']==pytest.approx(267.5)
    assert i['september_nwc']==pytest.approx(1051.3)
    first=f.iloc[0];q4=2487.8*1.3
    assert first.revenue==pytest.approx(9402.3+q4)
    assert first.gross_profit==pytest.approx(5912.8+q4*.63)
    assert first.operating_expenses==pytest.approx(1734.6+q4*.19)
    assert first.da==pytest.approx(70.3+q4*.009)
    assert first.ppe_capex==pytest.approx(184.9+q4*.025)
    assert first.hypothetical_intangible_reinvestment==pytest.approx(first.revenue*.005)
    assert f.fiscal_year.tolist()==[2026,2027,2028,2029,2030]
    assert f.status.eq(STATUS).all()
    assert '9M reported' in first.period_status
    assert first.discount_years==.25
    # Reconcile annual model to the elapsed-nine-month model, never calling that model actual FCFF.
    modeled_ytd_fcff=(4178.2*(1-.22)+70.3-184.9-9402.3*.005-(1051.3-267.5))
    assert first.annual_fcff-modeled_ytd_fcff==pytest.approx(first.dcf_included_fcff)
    assert first.dcf_period=='Q4 stub only'
    assert first.dcf_included_fcff!=first.annual_fcff
    for n,r in f.iterrows():
        assert r.operating_income==pytest.approx(r.gross_profit-r.operating_expenses)
        assert r.modeled_operating_taxes==pytest.approx(r.operating_income*r.tax_rate)
        assert r.nopat==pytest.approx(r.operating_income-r.modeled_operating_taxes)
        assert r.total_modeled_capex==pytest.approx(r.ppe_capex+r.hypothetical_intangible_reinvestment)
        assert r.annual_fcff==pytest.approx(r.nopat+r.da-r.total_modeled_capex-r.change_nwc)
        prior=i['opening_nwc'] if n==0 else f.iloc[n-1].operating_nwc_proxy
        assert r.change_nwc==pytest.approx(r.operating_nwc_proxy-prior)
        if n:assert r.revenue_growth==pytest.approx(s['growth_2027_2030'][n-1])


def test_dcf_discount_and_terminal_reinvestment_not_last_fcff_scaled():
    s,b=settings();f=forecast(load_inputs(),s,'Base');r,d=dcf(f,.10,.03,b)
    expected=sum(c/(1.1**t) for c,t in zip(f.dcf_included_fcff,[.25,1.25,2.25,3.25,4.25]))
    assert r['pv_forecast_fcff']==pytest.approx(expected)
    last=f.iloc[-1];rev=last.revenue*1.03
    terminal=(rev*(.63-.19)*.78+rev*.009-rev*.03-last.operating_nwc_proxy*.03)
    assert r['terminal_fcff']==pytest.approx(terminal)
    assert terminal!=pytest.approx(last.annual_fcff*1.03)
    assert r['terminal_value']==pytest.approx(terminal/(.10-.03))
    assert r['pv_terminal_value']==pytest.approx(r['terminal_value']/1.1**4.25)
    assert r['enterprise_value']==pytest.approx(expected+r['pv_terminal_value'])
    assert r['value_per_share'] is None and r['equity_value'] is None
    assert r['bridge_status']=='BLOCKED'
    assert 'diluted_shares' in r['bridge_reasons']


def test_synthetic_fcff_and_bridge_math():
    s,b=settings();s.update(gross_margin=.5,opex_ratio=.2,tax_rate=.2,da_ratio=0,
                            ppe_capex_ratio=0,intangible_reinvestment_ratio=0,nwc_ratio=0)
    i=dict(fy2025_revenue=1000,q4_2025_revenue=200,ytd_revenue=800,ytd_gross_profit=400,
           ytd_opex=160,ytd_da=0,ytd_ppe_capex=0,opening_nwc=0,september_nwc=0)
    r=forecast(i,s,'Synthetic').iloc[0]
    assert r.revenue==1060
    assert r.annual_fcff==pytest.approx(1060*.3*.8)
    assert r.dcf_included_fcff==pytest.approx(260*.3*.8)
    for field,v in zip(b['inputs'],[100,20,30,10,10]):
        b['inputs'][field].update(value=v,validated=True,source_reference='Synthetic test fixture only')
    bridge=equity_bridge(1000,b)
    assert bridge['equity_value']==1080 and bridge['value_per_share']==108
    assert 'ILLUSTRATIVE' in bridge['bridge_status']
    b['inputs']['diluted_shares']['validated']=False
    assert equity_bridge(1000,b)['value_per_share'] is None


@pytest.mark.parametrize('field,value',[
    ('gross_margin',None),('tax_rate',float('nan')),('opex_ratio',-1),('da_ratio',True),
    ('growth_2027_2030',[.1]),('q4_2026_revenue_yoy',-1),('wacc',.03),('terminal_growth',.10),
])
def test_invalid_or_missing_assumptions_fail(field,value):
    s,_=settings();s[field]=value
    with pytest.raises(ValueError):validate_scenario(s)


def test_missing_source_input_and_nwc_are_not_zero():
    s,_=settings();i=load_inputs();i['ytd_revenue']=None
    with pytest.raises(ValueError):forecast(i,s,'Missing')
    with pytest.raises(KeyError):operating_nwc({})
    s.pop('tax_rate')
    with pytest.raises(ValueError,match='Missing assumption'):validate_scenario(s)


@pytest.mark.parametrize('wacc,g',[(.03,.03),(.02,.03),(0,-.01),(float('inf'),.02)])
def test_invalid_discount_pairs_fail(wacc,g):
    s,b=settings();f=forecast(load_inputs(),s,'Base')
    with pytest.raises(ValueError):dcf(f,wacc,g,b)
    with pytest.raises(ValueError):sensitivity(f,[wacc],[g],b)


def test_sensitivity_direction_and_grid():
    s,b=settings();f=forecast(load_inputs(),s,'Base')
    table=sensitivity(f,[.08,.10,.12],[.02,.03,.04],b)
    assert len(table)==9 and table.value_per_share.isna().all()
    pivot=table.pivot(index='wacc',columns='terminal_growth',values='enterprise_value')
    assert (pivot.diff().dropna()<0).all().all()
    assert (pivot.diff(axis=1).iloc[:,1:]>0).all().all()


def test_bridge_missing_date_units_and_share_count():
    _,b=settings()
    for k in b['inputs']:
        b['inputs'][k].update(value=1,validated=True,source_reference='Synthetic only')
    b['reference_date']='2025-12-31'
    assert equity_bridge(100,b)['bridge_status']=='BLOCKED'
    b['reference_date']='2026-09-30';b['inputs']['diluted_shares']['value']=0
    with pytest.raises(ValueError):equity_bridge(100,b)
    b['inputs']['diluted_shares']['value']=1;b['inputs']['diluted_shares']['units']='shares'
    with pytest.raises(ValueError):equity_bridge(100,b)


def test_committed_outputs_match_current_model():
    config=json.loads(ASSUMPTIONS.read_text());b=json.loads(BRIDGE.read_text());i=load_inputs()
    forecasts=pd.read_csv(ROOT/'model_outputs/forecasts.csv')
    summaries=pd.read_csv(ROOT/'model_outputs/scenario_dcf.csv')
    for name,s in config['scenarios'].items():
        expected=forecast(i,s,name)
        saved=forecasts[forecasts.scenario.eq(name)].reset_index(drop=True)
        pd.testing.assert_frame_equal(saved,expected,check_dtype=False,rtol=1e-8)
        r,detail=dcf(expected,s['wacc'],s['terminal_growth'],b)
        saved_detail=pd.read_csv(ROOT/'model_outputs/discounted_cash_flows.csv')
        saved_detail=saved_detail[saved_detail.scenario.eq(name)].reset_index(drop=True)
        pd.testing.assert_frame_equal(saved_detail,detail,check_dtype=False,rtol=1e-8)
        expected_sensitivity=sensitivity(expected,config['sensitivity_wacc'],config['sensitivity_terminal_growth'],b)
        saved_sensitivity=pd.read_csv(ROOT/'model_outputs/sensitivity.csv')
        saved_sensitivity=saved_sensitivity[saved_sensitivity.scenario.eq(name)].reset_index(drop=True)
        # CSV represents intentionally missing per-share values as NaN.
        expected_sensitivity['value_per_share']=float('nan')
        pd.testing.assert_frame_equal(saved_sensitivity,expected_sensitivity,check_dtype=False,rtol=1e-8)
        assert summaries.set_index('scenario').loc[name,'enterprise_value']==pytest.approx(r['enterprise_value'])
    checks=pd.read_csv(ROOT/'model_outputs/arithmetic_checks.csv')
    assert len(checks)==60 and checks.status.eq('PASS').all()
    assert len(pd.read_csv(ROOT/'model_outputs/assumptions.csv'))==33
    assert summaries.value_per_share.isna().all()
    assert summaries.equity_value.isna().all()
    manifest=json.loads((ROOT/'model_outputs/manifest.json').read_text())
    for p,h in manifest['input_sha256'].items():
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
    with pytest.raises(ValueError,match='dedicated'):
        build(ROOT/'data/source')
