"""Validated interim comparisons and additive TTM income metrics, kept separate from annual FCF."""
import csv
import hashlib
import json
import math

import pandas as pd

from anet_research.quarterly import (
    DATA, ROOT, SOURCE_URL, ACCESSION, PERIODS, extract_statements, metric_summary, arithmetic_checks,
)
from anet_research.sec import load_verified_metrics

VIEW = '2026 Q3 / 9M 10-Q'
INCOME_FIELDS = ['revenue', 'cost_of_revenue', 'gross_profit', 'operating_expenses',
                 'operating_income', 'net_income']
DISPLAY_FIELDS = ['revenue', 'gross_profit', 'operating_income', 'net_income', 'diluted_eps']
ANNUAL_URL = 'https://www.sec.gov/Archives/edgar/data/1596532/000159653226000013/anet-20251231.htm'
TTM_PERIOD = 'TTM ended September 30, 2026 (October 1, 2025–September 30, 2026)'
FCF_BLOCK = 'BLOCKED: annual purchases include intangibles; interim purchases are PP&E-only. CapEx definitions must be reconciled.'
EPS_BLOCK = ('NOT CALCULATED: diluted EPS is not additive. Rounded period EPS and differing weighted-average '
             'diluted share counts require a validated TTM denominator and rounding analysis.')


def _serialized(rows):
    return [{k: '' if v is None else str(v) for k, v in row.items()} for row in rows]


def _read(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def load_interim():
    """Fail closed if source captures or reviewed CSV artifacts no longer reconcile."""
    meta = json.loads((DATA / 'anet_20260930_metadata.json').read_text())
    for name, key in [('source', 'source_capture_sha256'), ('filing_index', 'filing_index_capture_sha256')]:
        if hashlib.sha256((DATA / f'anet_20260930_{name}.txt').read_bytes()).hexdigest() != meta[key]:
            raise ValueError('Quarterly source snapshot hash mismatch; re-verification required.')
    if meta['source_url'] != SOURCE_URL or meta['accession'] != ACCESSION:
        raise ValueError('Unexpected quarterly provenance.')
    tables = extract_statements()
    for name, records in tables.items():
        if _read(DATA / f'anet_20260930_{name}.csv') != _serialized(records):
            raise ValueError(f'{name} CSV differs from the preserved SEC source.')
    checks = arithmetic_checks(tables)
    if any(row['status'] == 'DISCREPANCY' for row in checks):
        raise ValueError('Quarterly arithmetic discrepancy; review required.')
    records = metric_summary(tables)
    if _read(DATA / 'anet_20260930_metrics.csv') != _serialized(records):
        raise ValueError('Quarterly metrics differ from validated statement data.')
    frame = pd.DataFrame(records)
    for field in INCOME_FIELDS + ['diluted_eps', 'operating_cash_flow',
                                 'purchases_of_property_and_equipment_signed', 'analytical_fcf_ppe_only']:
        frame[field] = pd.to_numeric(frame[field], errors='raise')
    frame['verified'] = True
    frame['source_reference'] = '2026 Form 10-Q Part I Item 1: income printed p.2; cash flows printed p.5'
    frame['verification_status'] = 'Reconciled to preserved official SEC 10-Q rendering; hash and arithmetic checked'
    return frame, pd.DataFrame(tables['balance_sheet'])


def load_ttm_annual():
    meta = json.loads((DATA / 'anet_20260930_metadata.json').read_text())
    path = ROOT / 'data/verified_2023_2025.csv'
    if hashlib.sha256(path.read_bytes()).hexdigest() != meta['protected_file_sha256']['data/verified_2023_2025.csv']:
        raise ValueError('Annual verified input changed; re-verification required before TTM.')
    frame = load_verified_metrics()
    frame['income_units'] = 'USD millions'
    return frame


def numeric(value):
    if value is None or pd.isna(value):
        return None
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('Financial values must be finite or missing.')
    return result


def yoy(current, prior):
    current, prior = numeric(current), numeric(prior)
    return None if current is None or prior is None or prior <= 0 else current / prior - 1


def comparisons(frame):
    """Pair like-duration periods only; growth on reported diluted EPS is rounded."""
    rows = []
    for name, months, start in [('Q3', 3, '07-01'), ('9M', 9, '01-01')]:
        current, prior = frame.loc[frame.period.eq(f'{name} 2026')], frame.loc[frame.period.eq(f'{name} 2025')]
        if len(current) != 1 or len(prior) != 1:
            raise ValueError('Exactly one current and prior period required.')
        current, prior = current.iloc[0], prior.iloc[0]
        for row, year in [(current, 2026), (prior, 2025)]:
            if row.duration_months != months or row.period_start != f'{year}-{start}' or row.period_end != f'{year}-09-30':
                raise ValueError('Period duration or dates do not match comparison label.')
        for field in DISPLAY_FIELDS:
            a, b = numeric(current[field]), numeric(prior[field])
            rows.append(dict(period_type='Quarter (Q3)' if months == 3 else 'Nine months YTD (9M)',
                             metric=field, current_period=current.period_label, prior_period=prior.period_label,
                             current_value=a, prior_value=b, yoy_growth=yoy(a,b),
                             units='USD per share' if field == 'diluted_eps' else 'USD millions',
                             growth_note='Based on rounded reported EPS' if field == 'diluted_eps' else 'Current / prior − 1; positive prior required',
                             source_url=SOURCE_URL, source_reference='Form 10-Q Part I Item 1, printed p.2',
                             verification_status=current.verification_status))
    return pd.DataFrame(rows)


def ttm_income(annual, interim):
    """Compute each additive metric only when its three matching inputs are verified."""
    def unique(frame, mask):
        rows = frame.loc[mask]
        return rows.iloc[0] if len(rows) == 1 else None
    fy = unique(annual, annual.fiscal_year.eq(2025))
    current = unique(interim, interim.period.eq('9M 2026'))
    prior = unique(interim, interim.period.eq('9M 2025'))
    def verified(row, url):
        return (row is not None and str(row.get('verified', '')).lower() == 'true'
                and row.get('source_url') == url
                and isinstance(row.get('source_reference'), str) and bool(row['source_reference'].strip()))
    annual_ok = verified(fy, ANNUAL_URL) and fy.get('income_units') == 'USD millions'
    interim_ok = all(verified(r, SOURCE_URL)
                     and r.get('units') == 'USD millions except diluted EPS in USD per share'
                     and r.get('duration_months') == 9
                     and r.get('period_start') == f'{year}-01-01' and r.get('period_end') == f'{year}-09-30'
                     for r, year in [(current,2026),(prior,2025)])
    rows = []
    for field in INCOME_FIELDS:
        inputs = [numeric(row.get(field)) if row is not None else None for row in [fy,current,prior]]
        ready = annual_ok and interim_ok and all(v is not None for v in inputs)
        rows.append(dict(period=TTM_PERIOD, metric=field, fy2025=inputs[0], nine_months_2026=inputs[1],
                         nine_months_2025=inputs[2], value=inputs[0]+inputs[1]-inputs[2] if ready else None,
                         units='USD millions', status='VERIFIED INPUTS; analytical TTM' if ready else 'UNAVAILABLE: missing or unverified input / invalid period',
                         formula='FY2025 + 9M2026 − 9M2025',
                         annual_source_url=ANNUAL_URL, annual_source_reference='Local 2025 Form 10-K PDF p.73 (printed p.69)',
                         interim_source_url=SOURCE_URL, interim_source_reference='2026 Form 10-Q Part I Item 1, printed p.2'))
    for field, status, units in [('diluted_eps',EPS_BLOCK,'USD per share'),('free_cash_flow',FCF_BLOCK,'USD millions')]:
        rows.append(dict(rows[0], metric=field, fy2025=None, nine_months_2026=None, nine_months_2025=None,
                         value=None, units=units, status=status, formula='Not calculated'))
    return pd.DataFrame(rows)
