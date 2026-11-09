"""Reproducible illustrative FCFF model. No dashboard or historical data writes.

Run: python -m anet_research.valuation --output-dir model_outputs
All scenario values are hypotheses, not management guidance or fair-value conclusions.
"""
import argparse
import csv
import copy
import hashlib
import json
import math
from pathlib import Path

import pandas as pd

from anet_research.interim import load_interim, load_ttm_annual
from anet_research.quarterly import DATA, ROOT, SOURCE_URL

STATUS = 'HYPOTHETICAL / NOT YET VALIDATED'
ANNUAL_URL = 'https://www.sec.gov/Archives/edgar/data/1596532/000159653226000013/anet-20251231.htm'
ASSUMPTIONS = ROOT / 'data/valuation/assumptions.json'
BRIDGE = ROOT / 'data/valuation/equity_bridge.json'
PARAMETERS = {
    'q4_2026_revenue_yoy': ('Q4 2025 revenue derived from FY less 9M, then scenario growth', 'Validate Q4 demand, acceptance timing, seasonality; not guidance.'),
    'growth_2027_2030': ('Annual revenue growth rates for FY2027–FY2030', 'Validate market demand, customer budgets, adoption and share; no AI revenue attribution assumed.'),
    'gross_margin': ('Q4 FY2026 and subsequent full-year gross margin', 'Validate product/customer mix, pricing, component costs and competition.'),
    'opex_ratio': ('Operating expenses / revenue', 'Validate R&D, selling and administrative staffing and costs; includes reported stock compensation, no additional SBC add-back.'),
    'tax_rate': ('Normalized operating tax rate applied to EBIT', 'Reconcile statutory, geographic, cash/deferred tax and stock-compensation effects; not reported effective tax rate.'),
    'da_ratio': ('Future D&A / revenue; 9M 2026 reported D&A retained', 'Validate depreciation lives, amortization, asset base and acquisition effects.'),
    'ppe_capex_ratio': ('Future cash PP&E spending / revenue', 'Validate maintenance/growth investment and construction timing.'),
    'intangible_reinvestment_ratio': ('Hypothetical additional intangible cash reinvestment / revenue', 'Not observed intangible purchases; validate separately, including the elapsed 9M component in the annual forecast.'),
    'nwc_ratio': ('Year-end operating NWC proxy / annual revenue', 'Validate operating classification, supplier deposits, deferred costs/revenue, tax balances and seasonality.'),
    'wacc': ('Annual effective discount rate', 'Source a dated risk-free rate, beta, equity risk premium, cost of debt and target financing weights.'),
    'terminal_growth': ('Perpetual FCFF growth after FY2030', 'Validate mature growth, margins, reinvestment and return on capital; terminal assumptions are not evidence.'),
}


def finite(value, label):
    if value is None or isinstance(value, bool):
        raise ValueError(f'{label} requires a finite number; missing is not zero.')
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{label} requires a finite number.') from exc
    if not math.isfinite(result):
        raise ValueError(f'{label} requires a finite number.')
    return result


def validate_scenario(s):
    for key in PARAMETERS:
        if key not in s:
            raise ValueError(f'Missing assumption: {key}')
    growth = s['growth_2027_2030']
    if not isinstance(growth, list) or len(growth) != 4:
        raise ValueError('Four annual growth assumptions required.')
    for g in [s['q4_2026_revenue_yoy'], *growth]:
        if finite(g, 'revenue growth') <= -1:
            raise ValueError('Revenue growth must exceed -100%.')
    for key in ['gross_margin', 'opex_ratio', 'tax_rate', 'da_ratio', 'ppe_capex_ratio', 'intangible_reinvestment_ratio', 'nwc_ratio']:
        v = finite(s[key], key)
        if not 0 <= v <= 1:
            raise ValueError(f'{key} must be a fraction between zero and one.')
    validate_discount(s['wacc'], s['terminal_growth'])


def validate_discount(wacc, growth):
    wacc, growth = finite(wacc, 'WACC'), finite(growth, 'terminal growth')
    if not wacc > 0 or growth <= -1 or wacc <= growth:
        raise ValueError('Require WACC > terminal growth, WACC > 0 and terminal growth > -100%.')
    return wacc, growth


def operating_nwc(values):
    """Broad noncash current operating proxy; economic classification remains hypothetical."""
    assets = ['Accounts receivable, net', 'Inventories', 'Prepaid expenses and other current assets']
    liabilities = ['Accounts payable', 'Accrued liabilities', 'Deferred revenue', 'Other current liabilities']
    return sum(finite(values[k], k) for k in assets) - sum(finite(values[k], k) for k in liabilities)


def load_inputs():
    interim, balance = load_interim()  # source hash, statement and arithmetic checks
    annual = load_ttm_annual()  # reviewed annual CSV fingerprint and verified source flags
    fy = annual.loc[annual.fiscal_year.eq(2025)]
    ytd25 = interim.loc[interim.period.eq('9M 2025')]
    ytd26 = interim.loc[interim.period.eq('9M 2026')]
    if any(len(x) != 1 for x in [fy, ytd25, ytd26]):
        raise ValueError('Missing or duplicate historical input period.')
    fy, ytd25, ytd26 = fy.iloc[0], ytd25.iloc[0], ytd26.iloc[0]
    with (DATA / 'anet_20260930_cash_flow_statement.csv').open(newline='') as stream:
        cash = list(csv.DictReader(stream))
    da = [r for r in cash if r['period'] == '9M 2026' and r['source_label'] == 'Depreciation and amortization']
    if len(da) != 1:
        raise ValueError('Missing or duplicate D&A input.')
    nwc = {}
    for date in ['2025-12-31', '2026-09-30']:
        group = balance.loc[balance.period.eq(date)]
        if group.source_label.duplicated().any():
            raise ValueError('Duplicate balance-sheet label.')
        nwc[date] = operating_nwc(dict(zip(group.source_label, group.value)))
    result = dict(fy2025_revenue=fy.revenue, q4_2025_revenue=fy.revenue-ytd25.revenue,
                  ytd_revenue=ytd26.revenue, ytd_gross_profit=ytd26.gross_profit,
                  ytd_opex=ytd26.operating_expenses, ytd_da=finite(da[0]['value'], 'D&A'),
                  ytd_ppe_capex=abs(ytd26.purchases_of_property_and_equipment_signed),
                  opening_nwc=nwc['2025-12-31'], september_nwc=nwc['2026-09-30'])
    for key, value in result.items():
        result[key] = finite(value, key)
    if result['q4_2025_revenue'] <= 0:
        raise ValueError('Q4 2025 revenue anchor must be positive.')
    return result


def forecast(inputs, scenario, name):
    validate_scenario(scenario)
    s = scenario
    i = {k: finite(v,k) for k,v in inputs.items()}
    if i['fy2025_revenue'] <= 0:
        raise ValueError('Historical revenue must be positive.')
    records = []
    prior_revenue, prior_nwc = i['fy2025_revenue'], i['opening_nwc']
    for offset, year in enumerate(range(2026,2031)):
        if year == 2026:
            q4_revenue = i['q4_2025_revenue']*(1+s['q4_2026_revenue_yoy'])
            revenue = i['ytd_revenue']+q4_revenue
            gross = i['ytd_gross_profit']+q4_revenue*s['gross_margin']
            opex = i['ytd_opex']+q4_revenue*s['opex_ratio']
            da = i['ytd_da']+q4_revenue*s['da_ratio']
            ppe = i['ytd_ppe_capex']+q4_revenue*s['ppe_capex_ratio']
            period_status = '9M reported income/D&A/PP&E + modeled Q4; annual taxes/intangibles/NWC modeled'
        else:
            q4_revenue = None
            revenue = prior_revenue*(1+s['growth_2027_2030'][offset-1])
            gross, opex = revenue*s['gross_margin'], revenue*s['opex_ratio']
            da, ppe = revenue*s['da_ratio'], revenue*s['ppe_capex_ratio']
            period_status = 'Fully modeled annual estimate'
        ebit = gross-opex
        # Loss tax shields are assumed usable immediately: explicit, unvalidated simplification.
        taxes = ebit*s['tax_rate']
        nopat = ebit-taxes
        intangible = revenue*s['intangible_reinvestment_ratio']
        capex = ppe+intangible
        nwc = revenue*s['nwc_ratio']
        change_nwc = nwc-prior_nwc
        fcff = nopat+da-capex-change_nwc
        if year == 2026:
            q4_ebit = q4_revenue*(s['gross_margin']-s['opex_ratio'])
            q4_fcff = (q4_ebit*(1-s['tax_rate'])+q4_revenue*s['da_ratio']
                       -q4_revenue*(s['ppe_capex_ratio']+s['intangible_reinvestment_ratio'])
                       -(nwc-i['september_nwc']))
            dcf_cash = q4_fcff
        else:
            dcf_cash = fcff
        records.append(dict(scenario=name,fiscal_year=year,status=STATUS,period_status=period_status,
            revenue=revenue,revenue_growth=revenue/prior_revenue-1,gross_profit=gross,gross_margin=gross/revenue,
            operating_expenses=opex,opex_ratio=opex/revenue,operating_income=ebit,operating_margin=ebit/revenue,
            tax_rate=s['tax_rate'],modeled_operating_taxes=taxes,nopat=nopat,da=da,ppe_capex=ppe,
            hypothetical_intangible_reinvestment=intangible,total_modeled_capex=capex,
            operating_nwc_proxy=nwc,change_nwc=change_nwc,annual_fcff=fcff,
            dcf_included_fcff=dcf_cash,dcf_period='Q4 stub only' if year==2026 else 'Full forecast year',
            discount_years=offset+0.25,units='USD millions; growth/margins/rates are fractions',
            historical_source_url=SOURCE_URL,annual_source_url=ANNUAL_URL))
        prior_revenue, prior_nwc = revenue,nwc
    return pd.DataFrame(records)


def allocate_liquidity(allocation):
    """Allocate ONE reported cash/securities pool, including a reserve beyond cash."""
    amounts={}
    reasons=[]
    for key in ['reported_cash','reported_investments','operating_liquidity_reserve','investment_adjustments']:
        row=allocation.get(key,{})
        if (row.get('validated') is not True or row.get('value') is None
            or row.get('reporting_date') != '2026-09-30' or row.get('units') != 'USD millions'
            or not isinstance(row.get('source_reference'),str) or not row['source_reference'].strip()):
            reasons.append(key+': '+row.get('reason','Missing validated amount, source, date or units.'))
            continue
        amounts[key]=finite(row['value'],key)
        if amounts[key]<0:
            raise ValueError('Liquidity inputs must be nonnegative.')
    if reasons:
        return None,' | '.join(reasons)
    cash,invest,reserve,adjust=(amounts[k] for k in ['reported_cash','reported_investments','operating_liquidity_reserve','investment_adjustments'])
    if reserve+adjust>cash+invest:
        raise ValueError('Reserve/adjustments exceed the financial-asset pool.')
    excess=max(cash-reserve,0)
    remaining_invest=invest-max(reserve-cash,0)-adjust
    if remaining_invest<0:
        raise ValueError('Investment adjustments exceed eligible securities after reserve.')
    return {'excess_cash':excess,'nonoperating_investments':remaining_invest},''


def equity_bridge(ev, bridge):
    bridge=copy.deepcopy(bridge)
    if 'liquidity_allocation' in bridge:
        allocated,reason=allocate_liquidity(bridge['liquidity_allocation'])
        for key in ['excess_cash','nonoperating_investments']:
            bridge['inputs'][key].update(value=allocated[key] if allocated else None,
                validated=allocated is not None,reason=reason,
                source_reference='Derived from validated same-date disjoint cash/securities pool and reserve/adjustments' if allocated else '')
    required = ['excess_cash','nonoperating_investments','debt_and_debt_like','other_equity_claims','diluted_shares','other_nonoperating_assets']
    reasons = []
    values = {}
    if bridge.get('reference_date') != '2026-09-30':
        reasons.append('Balance-sheet/share dates must align with September 30, 2026 reference date.')
    for field in required:
        row=bridge.get('inputs',{}).get(field,{})
        if (row.get('validated') is not True or row.get('value') is None
                or not isinstance(row.get('source_reference'),str) or not row['source_reference'].strip()):
            reasons.append(f'{field}: '+row.get('reason','Missing validated value and source reference.'))
            continue
        if row.get('reporting_date','2026-09-30') != '2026-09-30':
            reasons.append(field+': reporting date mismatch.')
            continue
        if field=='diluted_shares' and row.get('basis') != 'point_in_time_fully_diluted':
            reasons.append('diluted_shares: valuation basis must be point_in_time_fully_diluted, not weighted-average EPS shares.')
            continue
        value=finite(row['value'],field)
        if value<0 or (field=='diluted_shares' and value<=0):
            raise ValueError('Bridge inputs must be nonnegative and diluted shares positive.')
        if row.get('units') != ('million shares' if field=='diluted_shares' else 'USD millions'):
            raise ValueError('Bridge unit mismatch.')
        values[field]=value
    if reasons:
        return dict(equity_value=None,value_per_share=None,bridge_status='BLOCKED',bridge_reasons=' | '.join(reasons))
    equity=ev+values['excess_cash']+values['nonoperating_investments']+values['other_nonoperating_assets']-values['debt_and_debt_like']-values['other_equity_claims']
    return dict(equity_value=equity,value_per_share=equity/values['diluted_shares'],
                bridge_status='ILLUSTRATIVE ONLY: scenario operating assumptions remain unvalidated',bridge_reasons='')


def dcf(frame, wacc, terminal_growth, bridge):
    wacc,g=validate_discount(wacc,terminal_growth)
    if list(frame.fiscal_year) != list(range(2026,2031)) or list(frame.discount_years) != [0.25,1.25,2.25,3.25,4.25]:
        raise ValueError('DCF requires ordered FY2026–FY2030 and September 30 end-year stub discounting.')
    detail=frame[['scenario','fiscal_year','dcf_period','dcf_included_fcff','discount_years']].copy()
    detail['status']=STATUS
    detail['valuation_reference_date']='2026-09-30'
    detail['units']='USD millions; discount years in years'
    detail['discount_factor']=[(1+wacc)**(-finite(t,'discount time')) for t in detail.discount_years]
    detail['pv_fcff']=[finite(c,'cash flow')*d for c,d in zip(detail.dcf_included_fcff,detail.discount_factor)]
    last=frame.iloc[-1]
    terminal_revenue=finite(last.revenue,'terminal revenue')*(1+g)
    terminal_nopat=terminal_revenue*finite(last.operating_margin,'terminal margin')*(1-finite(last.tax_rate,'terminal tax'))
    terminal_da=terminal_revenue*finite(last.da/last.revenue,'terminal D&A ratio')
    terminal_capex=terminal_revenue*finite(last.total_modeled_capex/last.revenue,'terminal CapEx ratio')
    terminal_change_nwc=finite(last.operating_nwc_proxy,'terminal NWC base')*g
    terminal_fcff=terminal_nopat+terminal_da-terminal_capex-terminal_change_nwc
    terminal_value=terminal_fcff/(wacc-g)
    pv_terminal=terminal_value*(1+wacc)**(-4.25)
    pv_cash=detail.pv_fcff.sum()
    ev=pv_cash+pv_terminal
    terminal_reinvestment=terminal_capex-terminal_da+terminal_change_nwc
    reinvestment_rate=terminal_reinvestment/terminal_nopat if terminal_nopat>0 else None
    implied_incremental_roc=g/reinvestment_rate if reinvestment_rate is not None and reinvestment_rate>0 and g>0 else None
    result=dict(scenario=frame.iloc[0].scenario,status=STATUS,valuation_reference_date='2026-09-30',
                wacc=wacc,terminal_growth=g,pv_forecast_fcff=pv_cash,terminal_revenue=terminal_revenue,
                terminal_nopat=terminal_nopat,terminal_da=terminal_da,terminal_capex=terminal_capex,
                terminal_change_nwc=terminal_change_nwc,terminal_fcff=terminal_fcff,
                terminal_net_reinvestment=terminal_reinvestment,terminal_reinvestment_rate=reinvestment_rate,
                implied_terminal_incremental_roc=implied_incremental_roc,
                terminal_economic_status="UNVALIDATED implied incremental return; not reported ROIC",
                terminal_value=terminal_value,pv_terminal_value=pv_terminal,enterprise_value=ev,
                terminal_value_share=pv_terminal/ev if ev else None,units='USD millions except per-share values in USD',
                **equity_bridge(ev,bridge))
    return result,detail


def sensitivity(frame, waccs, growths, bridge):
    rows=[]
    for w in waccs:
        for g in growths:
            # Invalid pairs fail explicitly; they are never valued.
            validate_discount(w,g)
            result,_=dcf(frame,w,g,bridge)
            rows.append({k:result[k] for k in ['scenario','status','wacc','terminal_growth','enterprise_value','value_per_share','bridge_status']})
    return pd.DataFrame(rows)


def build(output_dir):
    config=json.loads(ASSUMPTIONS.read_text())
    if config['status'] != STATUS or config['valuation_reference_date'] != '2026-09-30':
        raise ValueError('Unexpected model status or date.')
    if set(config['scenarios']) != {'Base','Bull','Bear'}:
        raise ValueError('Exactly Base, Bull and Bear scenarios are required.')
    bridge=json.loads(BRIDGE.read_text())
    inputs=load_inputs()
    forecasts=[];summaries=[];discounts=[];sensitivities=[];assumptions=[]
    for name,s in config['scenarios'].items():
        f=forecast(inputs,s,name)
        result,detail=dcf(f,s['wacc'],s['terminal_growth'],bridge)
        forecasts.append(f);summaries.append(result);discounts.append(detail)
        sensitivities.append(sensitivity(f,config['sensitivity_wacc'],config['sensitivity_terminal_growth'],bridge))
        for field,(definition,rationale) in PARAMETERS.items():
            assumptions.append(dict(scenario=name,driver=field,value=json.dumps(s[field]),status=STATUS,
                                    definition=definition,evidence_needed=rationale))
    input_rows=[]
    for field,value in inputs.items():
        derived = field in ['q4_2025_revenue','opening_nwc','september_nwc']
        input_rows.append(dict(input=field,value=value,units='USD millions',
            status='DERIVED PROXY / CLASSIFICATION UNVALIDATED' if 'nwc' in field else 'DERIVED FROM VERIFIED AMOUNTS' if derived else 'VERIFIED REPORTED INPUT',
            source_url=ANNUAL_URL+' ; '+SOURCE_URL if field=='q4_2025_revenue' else ANNUAL_URL if field=='fy2025_revenue' else SOURCE_URL,
            source_reference='10-K Item 8 p.69 less 10-Q Part I Item 1 p.2' if field=='q4_2025_revenue' else
                '10-K Item 8 p.69' if field=='fy2025_revenue' else '10-Q Part I Item 1 p.1 (dated balance-sheet inputs)' if 'nwc' in field else
                '10-Q Part I Item 1 p.5 (9M 2026)' if field in ['ytd_da','ytd_ppe_capex'] else '10-Q Part I Item 1 p.2 (9M 2026)'))
    residuals=[]
    for f in forecasts:
        for _,r in f.iterrows():
            for label,diff in [
                ('EBIT',r.operating_income-(r.gross_profit-r.operating_expenses)),
                ('NOPAT',r.nopat-r.operating_income*(1-r.tax_rate)),
                ('CapEx components',r.total_modeled_capex-r.ppe_capex-r.hypothetical_intangible_reinvestment),
                ('FCFF',r.annual_fcff-(r.nopat+r.da-r.total_modeled_capex-r.change_nwc)),
            ]:
                residuals.append(dict(scenario=r.scenario,fiscal_year=r.fiscal_year,check=label,
                    difference=diff,tolerance=1e-8,status='PASS' if abs(diff)<=1e-8 else 'FAIL'))
    if any(r['status']=='FAIL' for r in residuals):
        raise ValueError('Model arithmetic validation failed.')
    outputs={'historical_inputs.csv':pd.DataFrame(input_rows),'arithmetic_checks.csv':pd.DataFrame(residuals),'forecasts.csv':pd.concat(forecasts,ignore_index=True),'scenario_dcf.csv':pd.DataFrame(summaries),
             'discounted_cash_flows.csv':pd.concat(discounts,ignore_index=True),
             'sensitivity.csv':pd.concat(sensitivities,ignore_index=True),'assumptions.csv':pd.DataFrame(assumptions)}
    from anet_research.valuation_review import review_outputs
    outputs.update(review_outputs(config,bridge,inputs))
    # Never permit the reproducibility command to overwrite protected project directories.
    output_dir=Path(output_dir).resolve()
    if (ROOT/'model_outputs').is_symlink():
        raise ValueError('Output directory symlinks are not permitted.')
    approved=(ROOT/'model_outputs').resolve()
    if output_dir != approved:
        raise ValueError('Output directory must be the dedicated model_outputs directory.')
    output_dir.mkdir(exist_ok=True)
    for name in [*outputs, 'manifest.json']:
        if (output_dir/name).is_symlink():
            raise ValueError('Output symlinks are not permitted.')
    for name,table in outputs.items():
        table.to_csv(output_dir/name,index=False,float_format='%.10g')
    manifest=dict(status=STATUS,inputs=inputs,information_date_note=config['information_date_note'],
                  source_references=[SOURCE_URL+' (Part I Item 1 pp.1,2,5)',ANNUAL_URL+' (Item 8 pp.69,72)'],
                  input_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [
                      ASSUMPTIONS,BRIDGE,ROOT/'data/verified_2023_2025.csv',*sorted(DATA.glob('*')),
                      *sorted((ROOT/'data/valuation').glob('annual_*')),(ROOT/'data/valuation/bridge_evidence.json')] if p.is_file()})
    (output_dir/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return outputs


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=ROOT/'model_outputs')
    args=parser.parse_args()
    tables=build(args.output_dir)
    print(tables['scenario_dcf.csv'][['scenario','status','enterprise_value','bridge_status']].to_string(index=False))
