"""Offline Q3 2026 filing regression, source, arithmetic and missing-data checks."""
import csv
from decimal import Decimal
import hashlib
import json

import pytest

from anet_research.quarterly import (
    ROOT, DATA, SOURCE_URL, ACCESSION, FCF_DEFINITION, source_lines,
    number, extract_statements, metric_summary, arithmetic_checks, analytical_fcf,
)


def read_csv(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def serialized(rows):
    return [{k: '' if v is None else str(v) for k,v in row.items()} for row in rows]


def test_all_extracted_values_trace_to_preserved_official_source():
    tables = extract_statements()
    assert {name:len(rows) for name,rows in tables.items()} == {
        'income_statement':80, 'balance_sheet':52, 'cash_flow_statement':58}
    for name, rows in tables.items():
        stored = read_csv(DATA / f'anet_20260930_{name}.csv')
        assert stored == serialized(rows)
        for row in rows:
            assert row['source_url'] == SOURCE_URL
            assert row['accession'] == ACCESSION
            assert row['source_label'] and row['source_units'] and row['period_label']
            assert number(row['source_value']) == Decimal(row['value'])
            assert Decimal(row['value']).is_finite()
            assert row['status'] == 'reported'
    income = tables['income_statement']
    assert next(r for r in income if r['source_line']==189)['units'] == 'USD per share'
    assert next(r for r in income if r['source_line']==192)['units'] == 'million shares'
    assert next(r for r in income if r['source_line']==170)['units'] == 'USD millions'


def test_source_capture_complete_and_hashed_and_filing_metadata():
    meta=json.loads((DATA/'anet_20260930_metadata.json').read_text())
    for name,key in [('source','source_capture_sha256'),('filing_index','filing_index_capture_sha256')]:
        assert hashlib.sha256((DATA/f'anet_20260930_{name}.txt').read_bytes()).hexdigest()==meta[key]
    lines=source_lines()
    assert set(lines)==set(range(1910))
    assert lines[9]=='FORM 10-Q'
    assert 'September' in lines[16] and '2026' in lines[16]
    assert lines[1909]=='56' and lines[1892]=='SIGNATURES'
    assert 'Three Months' in lines[164] and 'Nine Months' in lines[165]
    assert '2026' in lines[166] and '2025' in lines[166]
    assert 'September 30, 2026' in lines[106] and 'December 31, 2025' in lines[106]
    assert 'Nine Months' in lines[297]
    index=(DATA/'anet_20260930_filing_index.txt').read_text()
    assert f"L15: {meta['filing_date']}" in index
    assert meta['filing_date']=='2026-11-04'
    assert f"L27: {meta['report_period_end']}" in index
    assert meta['accession']==ACCESSION and meta['source_url']==SOURCE_URL


@pytest.mark.parametrize('period,expected', [
    ('Q3 2026', ['3657.6','1331.9','2325.7','683.3','1642.4','1560.4','1.22',None,None,None]),
    ('Q3 2025', ['2308.3','818.1','1490.2','512.0','978.2','853.0','0.67',None,None,None]),
    ('9M 2026', ['9402.3','3489.5','5912.8','1734.6','4178.2','3796.2','2.98','3977.4','-184.9','3792.5']),
    ('9M 2025', ['6517.9','2313.0','4204.9','1381.7','2823.2','2555.6','2.00','3110.0','-82.5','3027.5']),
])
def test_key_figures_match_reviewed_statement_columns(period,expected):
    rows=metric_summary(extract_statements())
    row=next(r for r in rows if r['period']==period)
    fields=['revenue','cost_of_revenue','gross_profit','operating_expenses','operating_income','net_income',
            'diluted_eps','operating_cash_flow','purchases_of_property_and_equipment_signed','analytical_fcf_ppe_only']
    assert [row[f] for f in fields]==expected
    assert row['fcf_definition']==FCF_DEFINITION
    assert read_csv(DATA/'anet_20260930_metrics.csv')==serialized(rows)


def test_period_coverage_and_missing_values_never_inferred():
    tables=extract_statements()
    assert {r['period'] for r in tables['cash_flow_statement']}=={'9M 2026','9M 2025'}
    assert {r['period'] for r in tables['balance_sheet']}=={'2026-09-30','2025-12-31'}
    for row in metric_summary(tables):
        if row['duration_months']==3:
            assert row['operating_cash_flow'] is None
            assert row['purchases_of_property_and_equipment_signed'] is None
            assert row['analytical_fcf_ppe_only'] is None
            assert row['ppe_purchases_outflow_magnitude'] is None
            assert 'NOT REPORTED' in row['cash_flow_status']
            assert row['period_start'].endswith('07-01')
        else:
            assert row['period_start'].endswith('01-01')
            assert row['period_end'].endswith('09-30')
    assert analytical_fcf(None,Decimal('-1')) is None
    assert analytical_fcf(Decimal('1'),None) is None
    assert number('') is None
    assert number('—')==0
    assert number('(184.9)')==Decimal('-184.9')
    # Spending must reduce FCF, regardless of input sign convention.
    assert analytical_fcf(Decimal('100'),Decimal('-20'))==80
    assert analytical_fcf(Decimal('100'),Decimal('20'))==80
    assert analytical_fcf(Decimal('-10'),Decimal('-20'))==-30


def test_all_statement_identities_and_saved_check_report():
    checks=arithmetic_checks(extract_statements())
    assert len(checks)==56
    assert sum(c['status']=='PASS' for c in checks)==52
    assert sum(c['status']=='ROUNDING' for c in checks)==4
    assert all(c['check']=='Diluted EPS rounded to cents' for c in checks if c['status']=='ROUNDING')
    assert not any(c['status']=='DISCREPANCY' for c in checks)
    assert read_csv(ROOT/'docs/q3_2026_arithmetic_checks.csv')==serialized(checks)


def test_missing_source_value_fails_instead_of_filling(monkeypatch):
    import anet_research.quarterly as q
    lines=source_lines()
    lines[319]=lines[319].replace('(184.9)', '')
    monkeypatch.setattr(q,'source_lines',lambda:lines)
    with pytest.raises(ValueError,match='column count'):
        extract_statements()


def test_arithmetic_detects_discrepancy():
    tables=extract_statements()
    row=next(r for r in tables['income_statement'] if r['source_line']==170 and r['period']=='Q3 2026')
    row['value']='9999'
    checks=arithmetic_checks(tables)
    assert any(c['check']=='Revenue components' and c['status']=='DISCREPANCY' for c in checks)


def test_workbooks_and_annual_data_unchanged():
    expected={
        'ANET_Financial Model.xlsx':'571b693f69a6644c5cab649b169f191ab404f69c90c8d55e733dd827c07ad5b3',
        'data/source/ANET_Financial Model.xlsx':'571b693f69a6644c5cab649b169f191ab404f69c90c8d55e733dd827c07ad5b3',
        'data/verified_2023_2025.csv':'ee4a83d5039e1bc4786a7f2784fd24ac63ce712525e3697945472e03046f6f82',
        'app.py':'76f5e79c577a9cd5c73e1303d8ba5abf98a7826ded652a3a1aad64a229a254fc',
    }
    meta=json.loads((DATA/'anet_20260930_metadata.json').read_text())
    assert meta['protected_file_sha256']==expected
    # app.py is a historical pre-integration fingerprint in the extraction metadata.
    # Dashboard changes are now authorized; workbook and annual inputs remain protected.
    for name,digest in expected.items():
        if name != 'app.py':
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
