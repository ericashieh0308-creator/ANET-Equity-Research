"""Offline source evidence and audit overlays; no silent scenario recalibration."""
import copy
import csv
import hashlib
import json
import re

import pandas as pd

from anet_research.quarterly import ROOT, DATA, SOURCE_URL, source_lines
from anet_research.interim import load_interim, load_ttm_annual

K_URL='https://www.sec.gov/Archives/edgar/data/1596532/000159653226000013/anet-20251231.htm'
EVIDENCE=ROOT/'data/valuation/annual_supplement.csv'
ANNUAL_EXTRACTS=ROOT/'data/valuation/annual_source_extracts.json'
BRIDGE_EVIDENCE=ROOT/'data/valuation/bridge_evidence.json'


def source_values(page,label):
    lines=[line for line in page.splitlines() if line.strip().startswith(label+' ')]
    if len(lines)!=1:
        raise ValueError('Annual source label must match exactly once: '+label)
    return [float(v.replace(',','').replace('(','-').replace(')','')) for v in
            re.findall(r'\(?\d[\d,]*\.\d+\)?',lines[0].split(label,1)[1])]


def annual_supplement():
    capture=json.loads(ANNUAL_EXTRACTS.read_text())
    if capture['source_url']!=K_URL or hashlib.sha256((ROOT/'anet-2025_10K.pdf').read_bytes()).hexdigest()!=capture['source_pdf_sha256']:
        raise ValueError('Annual source PDF or provenance changed.')
    data=pd.read_csv(EVIDENCE)
    pages={'pretax_income':69,'tax_expense':69,'da':72,'sbc':72,'cash_taxes_paid':72}
    for _,row in data.iterrows():
        page=pages[row.metric]
        values=source_values(capture['pages'][str(page)],row.source_label)
        column={2025:0,2024:1,2023:2}[int(row.period[2:])]
        if len(values)!=3 or values[column]!=row.value or row.source_url!=K_URL or row.classification!='REPORTED' or row.units!='USD millions':
            raise ValueError('Annual supplement differs from source excerpt.')
    if len(data)!=15 or data[['period','metric']].duplicated().any():
        raise ValueError('Annual supplement coverage incomplete or duplicated.')
    return data,capture


def historical_evidence():
    from anet_research.valuation import operating_nwc
    supplement,capture=annual_supplement()
    annual=load_ttm_annual();interim,balance=load_interim()
    with (DATA/'anet_20260930_income_statement.csv').open(newline='') as f:income=list(csv.DictReader(f))
    with (DATA/'anet_20260930_cash_flow_statement.csv').open(newline='') as f:cash=list(csv.DictReader(f))
    def val(rows,period,line):
        selected=[float(r['value']) for r in rows if r['period']==period and int(r['source_line'])==line]
        if len(selected)>1:raise ValueError('Duplicate evidence input.')
        return selected[0] if selected else None
    records=[]
    for _,r in annual.iterrows():
        period='FY'+str(int(r.fiscal_year))
        extra=supplement[supplement.period.eq(period)].set_index('metric').value.to_dict()
        nwc=None
        if r.fiscal_year in [2024,2025]:
            column=0 if r.fiscal_year==2025 else 1
            labels=['Accounts receivable, net','Inventories','Prepaid expenses and other current assets','Accounts payable','Accrued liabilities','Deferred revenue','Other current liabilities']
            nwc=operating_nwc({label:source_values(capture['pages']['68'],label)[column] for label in labels})
        records.append(dict(period=period,duration_months=12,revenue=r.revenue,gross_profit=r.gross_profit,
            operating_expenses=r.operating_expenses,operating_income=r.operating_income,
            revenue_growth=None if pd.isna(r.revenue_growth_yoy) else r.revenue_growth_yoy,
            **extra,capital_purchases_signed=r.property_equipment_intangible_purchases,
            capex_scope='PP&E AND INTANGIBLES COMBINED',nwc_current_proxy=nwc,
            source_url=K_URL,source_reference='10-K Item 8 pp.68,69,72; PDF pp.72,73,76'))
    for _,r in interim.iterrows():
        period=r.period
        prior=interim.loc[interim.period.eq(period.replace('2026','2025'))]
        growth=r.revenue/prior.iloc[0].revenue-1 if '2026' in period else None
        group=balance[balance.period.eq('2026-09-30')]
        nwc=operating_nwc(dict(zip(group.source_label,group.value))) if period=='9M 2026' else None
        records.append(dict(period=period,duration_months=int(r.duration_months),revenue=r.revenue,
            gross_profit=r.gross_profit,operating_expenses=r.operating_expenses,operating_income=r.operating_income,
            revenue_growth=growth,pretax_income=val(income,period,184),tax_expense=val(income,period,185),
            da=val(cash,period,302),sbc=val(cash,period,303),cash_taxes_paid=None,
            capital_purchases_signed=None if pd.isna(r.purchases_of_property_and_equipment_signed) else r.purchases_of_property_and_equipment_signed,
            capex_scope='PP&E ONLY; 9M YTD' if r.duration_months==9 else 'NOT REPORTED FOR STANDALONE Q3',
            nwc_current_proxy=nwc,source_url=SOURCE_URL,source_reference='10-Q Part I Item 1 pp.1,2,5; Notes 5–7 pp.11–12'))
    frame=pd.DataFrame(records)
    for name,amount in [('gross_margin','gross_profit'),('operating_margin','operating_income'),('opex_ratio','operating_expenses'),('da_ratio','da'),('sbc_ratio','sbc')]:
        frame[name]=frame[amount]/frame.revenue
    frame['gaap_effective_tax_rate']=frame.tax_expense/frame.pretax_income
    frame['purchase_ratio']=frame.capital_purchases_signed.abs()/frame.revenue
    frame['nwc_proxy_to_period_revenue']=frame.nwc_current_proxy/frame.revenue
    frame['classification']='Amounts REPORTED; ratios and NWC proxy ANALYST_DERIVED; missing values not zero'
    frame['units']='USD millions; ratios fractions'
    frame['comparability_note']='Do not pool annual combined purchases with interim PP&E-only; NWC/9M sales is not an annual ratio; GAAP ETR is not normalized operating tax'
    return frame


def reviewed_bridge_evidence():
    _,balance=load_interim()
    facts=json.loads(BRIDGE_EVIDENCE.read_text())
    byid={r['id']:r for r in facts}
    for key,label in [('cash_and_equivalents','Cash and cash equivalents'),('marketable_securities','Marketable securities'),('other_current_liabilities','Other current liabilities'),('other_long_term_liabilities','Other long-term liabilities'),('noncurrent_deferred_revenue','Deferred revenue, non-current'),('other_assets','Other assets')]:
        row=balance.loc[balance.period.eq('2026-09-30') & balance.source_label.eq(label)]
        if len(row)!=1 or float(row.iloc[0].value)!=byid[key]['value']:
            raise ValueError('Bridge reported evidence disagrees with verified statement.')
    lines=source_lines()
    for r in facts:
        if r['classification']=='REPORTED' and r['snapshot_line'] is not None:
            token=r.get('raw_source_token') or ('—' if r['value']==0 else f"{r['value']:,.1f}")
            if token not in lines[r['snapshot_line']]:
                raise ValueError('Bridge source token changed: '+r['id'])
            if 'conversion_to_millions' in r and float(token)*r['conversion_to_millions']!=r['value']:
                raise ValueError('Bridge unit conversion mismatch.')
    if '1,263.4' not in lines[143] or '24.3' not in lines[584] or '1.5' not in lines[409]:
        raise ValueError('Share or restricted-cash source evidence changed.')
    if byid['basic_shares_point_in_time']['value']!=1263.4 or byid['unvested_rsus']['value']!=24.3 or byid['restricted_cash']['value']!=1.5:
        raise ValueError('Bridge share/restricted cash transcription changed.')
    return pd.DataFrame(facts)


def assumption_matrix(config,hist):
    from anet_research.valuation import PARAMETERS,STATUS
    assessment={
        'q4_2026_revenue_yoy':'Historical comparisons do not identify Q4 demand/acceptance. Keep 10/30/50% hypothetical; not guidance.',
        'growth_2027_2030':'No supported multiyear range. Deceleration is a hypothesis, not an empirical forecast.',
        'gross_margin':'Observed 61.95–64.56% across these periods; 62.9–64.1% is an evidence discussion window, not a validated future range. 60/65% are stress assumptions.',
        'opex_ratio':'Compare period mix and R&D investment; current 18–22% is not independently calibrated.',
        'tax_rate':'GAAP ETR varies with credits/deferred taxes; 22% normalized operating tax is unvalidated, not a reported rate.',
        'da_ratio':'Observed roughly 0.75–1.20% of sales is a historical calibration window only; 0.9% needs an asset/amortization schedule.',
        'ppe_capex_ratio':'9M PP&E ratios differ from annual combined amounts. 2.5–3% requires construction/maintenance evidence, not a splice.',
        'intangible_reinvestment_ratio':'No cash-purchase split validates 0.5%. Compare explicit omitted-intangible and extra-budget cases, neither a verified reconciliation.',
        'nwc_ratio':'8–11% targets are unvalidated; deferred revenue maturity and deposits can change proxy materially.',
        'wacc':'No dated risk-free rate, beta, ERP, debt cost or financing weights validated. 9–12% remains illustrative.',
        'terminal_growth':'No supported perpetual-growth range; inspect implied incremental return and reinvestment before accepting 2–3.5%.',
    }
    mapping={'gross_margin':'gross_margin','opex_ratio':'opex_ratio','tax_rate':'gaap_effective_tax_rate','da_ratio':'da_ratio','q4_2026_revenue_yoy':'revenue_growth','growth_2027_2030':'revenue_growth'}
    rows=[]
    for case,s in config['scenarios'].items():
        for key,(_,needed) in PARAMETERS.items():
            col=mapping.get(key)
            observed=hist[col].dropna() if col else pd.Series(dtype=float)
            evidence='; '.join(f'{r.period}={r[col]:.6g}' for _,r in hist.iterrows() if col and pd.notna(r[col]))
            if key=='ppe_capex_ratio':evidence='Annual combined: '+str(hist[hist.duration_months.eq(12)][['period','purchase_ratio']].values.tolist())+'; 9M PP&E-only: '+str(hist[hist.duration_months.eq(9)][['period','purchase_ratio']].values.tolist())
            rows.append(dict(scenario=case,driver=key,assumed_value=json.dumps(s[key]),assumption_classification=STATUS,
                historical_evidence=evidence or 'SOURCE GAP / economic classification required',
                observed_min=observed.min() if len(observed) else None,observed_max=observed.max() if len(observed) else None,
                evidence_classification='REPORTED underlying figures; ANALYST_DERIVED ratios; NOT a forecast interval',
                assessment=assessment[key],evidence_needed=needed,source_url=K_URL+' ; '+SOURCE_URL,
                source_reference='10-K Item 8 pp.68,69,72; 10-Q Part I Item 1 pp.1,2,5 and Notes 3–7; no source validates hypothetical scenario rates'))
    return pd.DataFrame(rows)


def review_outputs(config,bridge,inputs):
    from anet_research.valuation import forecast,dcf,STATUS
    hist=historical_evidence();facts=reviewed_bridge_evidence()
    # Ensure the bridge uses the exact reported cash/security pool, not the cash-equivalent subset.
    allocation=bridge.get('liquidity_allocation')
    if allocation:
        for key,id in [('reported_cash','cash_and_equivalents'),('reported_investments','marketable_securities')]:
            if allocation[key]['value']!=float(facts.set_index('id').loc[id,'value']):
                raise ValueError('Configured liquidity pool differs from verified source.')
    stub=[];alternatives=[];terminal=[]
    for name,s in config['scenarios'].items():
        f=forecast(inputs,s,name);result,_=dcf(f,s['wacc'],s['terminal_growth'],bridge)
        first=f.iloc[0]
        ytd_nopat=(inputs['ytd_gross_profit']-inputs['ytd_opex'])*(1-s['tax_rate'])
        ytd_intangible=inputs['ytd_revenue']*s['intangible_reinvestment_ratio']
        ytd_nwc=inputs['september_nwc']-inputs['opening_nwc']
        ytd_fcff=ytd_nopat+inputs['ytd_da']-inputs['ytd_ppe_capex']-ytd_intangible-ytd_nwc
        residual=first.annual_fcff-ytd_fcff-first.dcf_included_fcff
        if abs(residual)>1e-8:raise ValueError('Annual/stub reconciliation failed.')
        stub.append(dict(scenario=name,status=STATUS,modeled_9m_nopat=ytd_nopat,modeled_9m_intangible_budget=ytd_intangible,
            derived_9m_nwc_change=ytd_nwc,modeled_9m_fcff_NOT_ACTUAL=ytd_fcff,annual_forecast_fcff=first.annual_fcff,
            q4_only_dcf_fcff=first.dcf_included_fcff,reconciliation_residual=residual,check_status='PASS',
            note='9M tax/intangible/NWC economics modeled; only Q4 cash included at t=0.25; no SBC add-back or lease capitalization'))
        for treatment,rate,note in [
            ('EXTRA_INTANGIBLE_BUDGET',s['intangible_reinvestment_ratio'],'Current scenario: additional budget not observed intangible cash'),
            ('PP&E_ONLY_SCOPE',0.0,'Intangible reinvestment deliberately omitted, NOT assumed reported zero; incomplete total FCFF if intangible investment required')]:
            alt=copy.deepcopy(s);alt['intangible_reinvestment_ratio']=rate
            table=forecast(inputs,alt,name);value,_=dcf(table,alt['wacc'],alt['terminal_growth'],bridge)
            alternatives.append(dict(scenario=name,treatment=treatment,status=STATUS,intangible_budget_ratio=rate,
                enterprise_value=value['enterprise_value'],value_per_share=None,scope_note=note))
        terminal.append({k:result[k] for k in ['scenario','status','terminal_growth','terminal_nopat','terminal_da','terminal_capex','terminal_change_nwc','terminal_fcff','terminal_net_reinvestment','terminal_reinvestment_rate','implied_terminal_incremental_roc','terminal_economic_status']})
    _,balances=load_interim()
    nwc=[]
    for date,current in [('2025-12-31',inputs['opening_nwc']),('2026-09-30',inputs['september_nwc'])]:
        deferred=float(balances[balances.period.eq(date)&balances.source_label.eq('Deferred revenue, non-current')].iloc[0].value)
        nwc.append(dict(date=date,current_only_proxy=current,noncurrent_deferred_revenue=deferred,
                       inclusive_proxy=current-deferred,status='ANALYST_DERIVED classifications; neither economic definition validated',
                       source_url=SOURCE_URL,source_reference='10-Q Part I Item 1 p.1; Note 3 pp.9–10',
                       note='No alternative EV: forecast target must be recalibrated with changed classification; no raw balance double deduction.'))
    return {'historical_evidence.csv':hist,'assumption_evidence_matrix.csv':assumption_matrix(config,hist),
            'bridge_evidence.csv':facts,'stub_audit.csv':pd.DataFrame(stub),
            'capex_alternatives.csv':pd.DataFrame(alternatives),'nwc_classifications.csv':pd.DataFrame(nwc),
            'terminal_economics.csv':pd.DataFrame(terminal)}
