"""Offline extraction of the preserved web-rendered official Q3 2026 10-Q.

This is a fixed-layout extraction for this filing, not a general SEC parser.
It never loads, changes, or concatenates the annual research series.
"""
from decimal import Decimal
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/quarterly'
SOURCE_URL = 'https://www.sec.gov/Archives/edgar/data/1596532/000159653226000254/anet-20260930.htm'
ACCESSION = '0001596532-26-000254'
FCF_DEFINITION = 'Analytical FCF after purchases of property and equipment (PP&E-only)'
PERIODS = [('Q3 2026', '2026-07-01', '2026-09-30', 'Three Months Ended September 30, 2026', 3),
           ('Q3 2025', '2025-07-01', '2025-09-30', 'Three Months Ended September 30, 2025', 3),
           ('9M 2026', '2026-01-01', '2026-09-30', 'Nine Months Ended September 30, 2026', 9),
           ('9M 2025', '2025-01-01', '2025-09-30', 'Nine Months Ended September 30, 2025', 9)]
SPECS = {
    'income_statement': (159, 161, 2, 167, 193, PERIODS),
    'balance_sheet': (102, 104, 1, 108, 149, [
        ('2026-09-30', '', '2026-09-30', 'September 30, 2026', 0),
        ('2025-12-31', '', '2025-12-31', 'December 31, 2025', 0)]),
    'cash_flow_statement': (293, 295, 5, 299, 334, PERIODS[2:]),
}


def source_lines():
    text = (DATA / 'anet_20260930_source.txt').read_text()
    return {int(n): line for n, line in re.findall(r'^L(\d+): ?(.*)$', text, re.M)}


def number(display):
    """Preserve reported dash in source_value; numeric nil is zero, not missing."""
    value = display.strip().replace(',', '')
    if not value:
        return None
    if value == '—':
        return Decimal('0')
    if value.startswith('(') and value.endswith(')'):
        value = '-' + value[1:-1]
    result = Decimal(value)
    if not result.is_finite():
        raise ValueError('Non-finite source value')
    return result


def extract_statements():
    lines = source_lines()
    tables = {}
    for name, (title, unit_line, page, start, stop, periods) in SPECS.items():
        rows, section = [], ''
        for line_no in range(start, stop):
            cells = [cell.strip() for cell in lines[line_no].split('|')]
            label = cells[0]
            values = [cell for cell in cells[1:] if cell and cell != '$']
            if not label:
                continue
            if not values:
                if label.endswith(':') or label in ('ASSETS', 'LIABILITIES AND STOCKHOLDERS’ EQUITY'):
                    section = label
                continue
            if len(values) != len(periods):
                raise ValueError(f'Unexpected source column count at L{line_no}')
            for col, (period, begin, end, period_label, months) in enumerate(periods):
                raw = values[col]
                value = number(raw)
                unit = 'USD per share' if section == 'Net income per share:' else 'million shares' if section.startswith('Weighted-average') else 'USD millions'
                rows.append(dict(statement=lines[title], source_section=section, source_label=label,
                                 period=period, period_label=period_label, period_start=begin, period_end=end,
                                 duration_months=months, source_value=raw, value=str(value), units=unit,
                                 source_units=lines[unit_line], source_page=page, source_line=line_no,
                                 source_column=col, source_url=SOURCE_URL, accession=ACCESSION,
                                 status='reported'))
        tables[name] = rows
    return tables


def analytical_fcf(operating_cash_flow, signed_purchases):
    """Subtract spending magnitude, keeping original signed purchases separate."""
    if operating_cash_flow is None or signed_purchases is None:
        return None
    return operating_cash_flow - abs(signed_purchases)


def metric_summary(tables):
    income = {(r['source_line'], r['period']): r['value'] for r in tables['income_statement']}
    cash = {(r['source_line'], r['period']): r['value'] for r in tables['cash_flow_statement']}
    rows = []
    for period, start, end, label, months in PERIODS:
        row = dict(period=period, period_label=label, period_start=start, period_end=end, duration_months=months,
                   units='USD millions except diluted EPS in USD per share', source_url=SOURCE_URL,
                   accession=ACCESSION, income_source_page=2, cash_flow_source_page=5,
                   fcf_definition=FCF_DEFINITION)
        for metric, line in [('revenue', 170), ('cost_of_revenue', 174), ('gross_profit', 175),
                             ('operating_expenses', 181), ('operating_income', 182), ('net_income', 186),
                             ('diluted_eps', 189)]:
            row[metric] = income[line, period]
        ocf, purchase = cash.get((314, period)), cash.get((319, period))
        row['operating_cash_flow'] = ocf
        row['purchases_of_property_and_equipment_signed'] = purchase
        row['ppe_purchases_outflow_magnitude'] = str(abs(Decimal(purchase))) if purchase is not None else None
        fcf = analytical_fcf(Decimal(ocf) if ocf is not None else None, Decimal(purchase) if purchase is not None else None)
        row['analytical_fcf_ppe_only'] = str(fcf) if fcf is not None else None
        row['cash_flow_status'] = 'reported 9M YTD; FCF analytical' if months == 9 else 'NOT REPORTED: standalone Q3 cash flows and FCF unavailable; not inferred'
        rows.append(row)
    return rows


def arithmetic_checks(tables):
    """Reported minus recomputed. Rounding bounds reflect each printed operand."""
    checks = []
    def check(table, period, label, total, terms, *, eps=False):
        rows = {int(r['source_line']): Decimal(r['value']) for r in tables[table] if r['period'] == period}
        reported = rows[total]
        computed = rows[terms[0][0]] / rows[terms[1][0]] if eps else sum((rows[n] * sign for n, sign in terms), Decimal(0))
        difference = reported - computed
        tolerance = Decimal('0.0051') if eps else Decimal('0.05') * (len(terms) + 1)
        checks.append(dict(statement=table, period=period, check=label, reported=str(reported),
                           recomputed=str(computed), difference=str(difference), tolerance=str(tolerance),
                           status='PASS' if difference == 0 else 'ROUNDING' if abs(difference) <= tolerance else 'DISCREPANCY',
                           source_page=SPECS[table][2], source_lines=','.join(map(str, [total] + [n for n, _ in terms]))))
    for period, *_ in PERIODS:
        for label, total, terms in [
            ('Revenue components',170,[(168,1),(169,1)]),
            ('Cost components',174,[(172,1),(173,1)]),
            ('Gross profit',175,[(170,1),(174,-1)]),
            ('Operating expenses',181,[(177,1),(178,1),(179,1)]),
            ('Operating income',182,[(175,1),(181,-1)]),
            ('Pretax income',184,[(182,1),(183,1)]),
            ('Net income',186,[(184,1),(185,-1)]),
        ]: check('income_statement',period,label,total,terms)
        check('income_statement',period,'Diluted EPS rounded to cents',189,[(186,1),(192,1)],eps=True)
    for period in ['2026-09-30','2025-12-31']:
        for label,total,terms in [
            ('Current assets',115,[(n,1) for n in range(110,115)]),
            ('Total assets',123,[(n,1) for n in [115,116,118,121,122]]),
            ('Current liabilities',133,[(n,1) for n in [126,127,129,132]]),
            ('Total liabilities',139,[(n,1) for n in [133,136,138]]),
            ('Equity components',147,[(n,1) for n in range(142,147)]),
            ('Liabilities plus equity',148,[(139,1),(147,1)]),
            ('Assets equal liabilities plus equity',123,[(148,1)]),
        ]: check('balance_sheet',period,label,total,terms)
    for period in ['9M 2026','9M 2025']:
        for label,total,terms in [
            ('Operating cash flow',314,[(n,1) for n in [300,302,303,304,305,307,308,309,310,311,312,313]]),
            ('Investing cash flow',322,[(n,1) for n in range(316,322)]),
            ('Financing cash flow',329,[(n,1) for n in range(325,329)]),
            ('Net cash change',331,[(n,1) for n in [314,322,329,330]]),
            ('Cash roll-forward',333,[(332,1),(331,1)]),
        ]: check('cash_flow_statement',period,label,total,terms)
        income = next(r for r in tables['income_statement'] if r['period']==period and r['source_line']==186)
        cash = next(r for r in tables['cash_flow_statement'] if r['period']==period and r['source_line']==300)
        if income['value'] != cash['value']:
            raise ValueError('Income statement and cash-flow net income disagree')
    return checks
