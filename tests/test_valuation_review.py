"""Review evidence, liquidity allocation, dilution basis and audit overlays."""
import copy
import json

import pandas as pd
import pytest

from anet_research.valuation import (ROOT,ASSUMPTIONS,BRIDGE,load_inputs,forecast,dcf,
                                    allocate_liquidity,equity_bridge,build)
from anet_research.valuation_review import historical_evidence,reviewed_bridge_evidence,review_outputs,annual_supplement


def configuration():
    return json.loads(ASSUMPTIONS.read_text()),json.loads(BRIDGE.read_text())


def test_historical_reported_and_derived_evidence():
    h=historical_evidence().set_index('period')
    assert len(h)==7
    assert h.loc['FY2023','pretax_income']==2422
    assert h.loc['FY2023','tax_expense']==334.7
    assert h.loc['FY2024','da']==62
    assert h.loc['FY2025','sbc']==439.2
    assert h.loc['FY2024','nwc_current_proxy']==pytest.approx(875.2)
    assert h.loc['FY2025','nwc_current_proxy']==pytest.approx(267.5)
    assert h.loc['9M 2026','da']==70.3
    assert h.loc['9M 2026','sbc']==379.4
    assert h.loc['9M 2026','gaap_effective_tax_rate']==pytest.approx(895/4691.2)
    assert pd.isna(h.loc['FY2023','nwc_current_proxy'])
    assert pd.isna(h.loc['Q3 2026','capital_purchases_signed'])
    assert pd.isna(h.loc['Q3 2026','da'])
    assert h.loc['FY2025','capex_scope']=='PP&E AND INTANGIBLES COMBINED'
    assert h.loc['9M 2026','capex_scope']=='PP&E ONLY; 9M YTD'


def test_bridge_evidence_is_not_an_automatic_equity_bridge():
    f=reviewed_bridge_evidence().set_index('id')
    assert f.loc['cash_and_equivalents','value']==2288.1
    assert f.loc['marketable_securities','value']==12070.9
    assert f.loc['restricted_cash','value']==1.5
    assert f.loc['basic_shares_point_in_time','value']==1263.4
    assert f.loc['unvested_rsus','value']==24.3
    assert f.loc['historical_operating_lease_payments','reporting_date']=='2025-12-31'
    _,bridge=configuration()
    result=equity_bridge(100,bridge)
    assert result['bridge_status']=='BLOCKED'
    assert result['value_per_share'] is None
    for missing in ['operating_liquidity_reserve','investment_adjustments','debt_and_debt_like','other_equity_claims','diluted_shares','other_nonoperating_assets']:
        assert missing in result['bridge_reasons']


def liquidity(reserve,adjust=0):
    _,b=configuration();a=b['liquidity_allocation']
    for k,v in [('reported_cash',100),('reported_investments',200),('operating_liquidity_reserve',reserve),('investment_adjustments',adjust)]:
        a[k].update(value=v,validated=True,source_reference='Synthetic test evidence')
    return a


@pytest.mark.parametrize('reserve,adjust,cash,invest',[(20,10,80,190),(150,10,0,140),(300,0,0,0)])
def test_disjoint_liquidity_pool_no_double_count(reserve,adjust,cash,invest):
    result,reason=allocate_liquidity(liquidity(reserve,adjust))
    assert not reason and result=={'excess_cash':cash,'nonoperating_investments':invest}
    assert sum(result.values())==300-reserve-adjust


def test_unknown_is_not_zero_and_liquidity_invalid_inputs():
    a=liquidity(0)
    a['investment_adjustments']['value']=None
    assert allocate_liquidity(a)[0] is None
    a=liquidity(20);a['reported_investments']['reporting_date']='2025-12-31'
    assert allocate_liquidity(a)[0] is None
    with pytest.raises(ValueError):allocate_liquidity(liquidity(301))
    with pytest.raises(ValueError):allocate_liquidity(liquidity(-1))
    with pytest.raises(ValueError):allocate_liquidity(liquidity(20,201))


@pytest.mark.parametrize('basis',['weighted_average_eps','unresolved',None])
def test_eps_shares_cannot_be_promoted_by_validation_flag_alone(basis):
    _,b=configuration();b.pop('liquidity_allocation')
    for r in b['inputs'].values():r.update(value=1,validated=True,source_reference='Synthetic fixture')
    b['inputs']['diluted_shares']['basis']=basis
    r=equity_bridge(100,b)
    assert r['value_per_share'] is None
    assert 'point_in_time_fully_diluted' in r['bridge_reasons']


def test_stub_terminal_and_capex_alternatives_do_not_recalibrate_base():
    config,b=configuration();i=load_inputs();tables=review_outputs(config,b,i)
    assert tables['stub_audit.csv'].check_status.eq('PASS').all()
    assert tables['stub_audit.csv'].reconciliation_residual.abs().max()<1e-8
    assert len(tables['capex_alternatives.csv'])==6
    for name,s in config['scenarios'].items():
        value,_=dcf(forecast(i,s,name),s['wacc'],s['terminal_growth'],b)
        alt=tables['capex_alternatives.csv'].query('scenario == @name').set_index('treatment')
        assert alt.loc['EXTRA_INTANGIBLE_BUDGET','enterprise_value']==pytest.approx(value['enterprise_value'])
        assert alt.loc['PP&E_ONLY_SCOPE','enterprise_value']>value['enterprise_value']
        assert 'NOT assumed reported zero' in alt.loc['PP&E_ONLY_SCOPE','scope_note']
        terminal=tables['terminal_economics.csv'].set_index('scenario').loc[name]
        assert terminal.terminal_net_reinvestment==pytest.approx(terminal.terminal_capex-terminal.terminal_da+terminal.terminal_change_nwc)
        assert terminal.implied_terminal_incremental_roc==pytest.approx(s['terminal_growth']/terminal.terminal_reinvestment_rate)
    n=tables['nwc_classifications.csv'].set_index('date')
    assert n.loc['2025-12-31','inclusive_proxy']==pytest.approx(-1102.3)
    assert n.loc['2026-09-30','inclusive_proxy']==pytest.approx(-686)
    assert n.loc['2026-09-30','current_only_proxy']-n.loc['2025-12-31','current_only_proxy']==pytest.approx(783.8)
    assert n.loc['2026-09-30','inclusive_proxy']-n.loc['2025-12-31','inclusive_proxy']==pytest.approx(416.3)


def test_evidence_transcription_and_saved_review_tables(monkeypatch):
    import anet_research.valuation_review as review
    config,b=configuration();tables=review_outputs(config,b,load_inputs())
    for name,expected in tables.items():
        actual=pd.read_csv(ROOT/'model_outputs'/name, dtype={'raw_source_token': str})
        expected=expected.where(pd.notna(expected),float('nan'))
        pd.testing.assert_frame_equal(actual,expected,check_dtype=False,rtol=1e-8)
    data,_=annual_supplement()
    real_read=review.pd.read_csv
    def tampered(path,*args,**kwargs):
        result=real_read(path,*args,**kwargs)
        if str(path).endswith('annual_supplement.csv'):result.loc[0,'value']=0
        return result
    monkeypatch.setattr(review.pd,'read_csv',tampered)
    with pytest.raises(ValueError,match='differs'):annual_supplement()
