"""PDF regression and source/data traceability checks (optional report extras)."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

pdf = pytest.importorskip('pymupdf', reason='Install requirements-report.txt for PDF validation')
pytest.importorskip('reportlab', reason='Install requirements-report.txt for report generation')
ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT/'reports/ANET_Equity_Research_2026-11-08.pdf'


def test_report_pages_glyphs_bounds_and_headers():
    doc=pdf.open(PATH)
    headings=['Arista Networks (NYSE: ANET)','Business, demand and competition',
              'Historical financial performance','Cash conversion and principal risks',
              'Preliminary hypotheses and forecast drivers','Forecast construction and FCFF methodology',
              'Scenario enterprise valuation and sensitivity','Limitations, sources and reproducibility']
    for n,page in enumerate(doc):
        text=page.get_text()
        assert headings[n] in text
        assert len(text)>1500  # No accidental blank or overflow-only page.
        assert not any(x in text for x in ['\ufffd','\u25a0','{{','---PAGE---'])
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                for span in line['spans']:
                    x0,y0,x1,y1=span['bbox']
                    assert 40<=x0<x1<=556 and 12<=y0<y1<=824,span
        assert page.get_fonts()
        for font in page.get_fonts():
            if 'DejaVu' in font[3]:assert font[1]=='ttf' and doc.extract_font(font[0])[3]
    assert len(doc)==8
    spans=[span for b in doc[5].get_text('dict')['blocks'] for line in b.get('lines',[]) for span in line['spans']]
    assert any(s['text']=='FY2026E' and s['color']==0xffffff for s in spans)


def test_report_values_sources_and_required_disclosures():
    doc=pdf.open(PATH);text=' '.join(' '.join(p.get_text().split()) for p in doc)
    values=pd.read_csv(ROOT/'model_outputs/scenario_dcf.csv')
    for x in values.enterprise_value:assert f'{x:,.1f}' in text
    annual=pd.read_csv(ROOT/'data/verified_2023_2025.csv')
    for key in ['revenue','gross_profit','operating_income','net_income']:
        for x in annual[key]:assert f'{x:,.1f}' in text
    forecasts=pd.read_csv(ROOT/'model_outputs/forecasts.csv')
    for key in ['revenue','operating_income','modeled_operating_taxes','nopat','da','ppe_capex','annual_fcff','dcf_included_fcff']:
        for x in forecasts.loc[forecasts.scenario.eq('Base'),key]:assert f'{x:,.1f}' in text
    grid=pd.read_csv(ROOT/'model_outputs/sensitivity.csv')
    for x in grid.loc[grid.scenario.eq('Base'),'enterprise_value']:assert f'{x:,.1f}' in text
    for phrase in ['HYPOTHETICAL / NOT YET VALIDATED','BLOCKED','November 4, 2026',
                   'PP&E-only','retrospective','period averages','No TTM diluted EPS',
                   'not market capitalizations','FCFF = EBIT']:
        assert phrase in text
    urls={link.get('uri') for page in doc for link in page.get_links() if link.get('uri')}
    assert len(urls)==7
    assert sum(u.startswith('https://www.sec.gov/Archives/') for u in urls)==3
    assert sum('/blob/ef5c8b0/docs/' in u for u in urls)==4


def test_report_manifest_and_deterministic_rebuild():
    manifest=json.loads((ROOT/'reports/report_manifest.json').read_text())
    for name,digest in manifest['input_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    before=PATH.read_bytes()
    assert hashlib.sha256(before).hexdigest()==manifest['pdf_sha256']
    subprocess.run([sys.executable,str(ROOT/'scripts/build_research_report.py')],cwd=ROOT,check=True,capture_output=True)
    assert PATH.read_bytes()==before
