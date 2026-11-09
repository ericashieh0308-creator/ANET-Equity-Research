"""Offline, data-linked eight-page portfolio report. Run from any directory."""
from pathlib import Path
import hashlib
import json
import sys
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.graphics.shapes import Drawing, Rect, String, Line

OUT = ROOT / 'reports'
SOURCE = OUT / 'anet_equity_research.md'
PDF = OUT / 'ANET_Equity_Research_2026-11-08.pdf'
NAVY = colors.HexColor('#15324F')
TEAL = colors.HexColor('#147D85')
GRAY = colors.HexColor('#526171')
WIDTH = 503.28
INPUTS = ['reports/anet_equity_research.md','scripts/build_research_report.py',
          'data/verified_2023_2025.csv','data/quarterly/anet_20260930_metrics.csv',
          'data/valuation/assumptions.json','model_outputs/forecasts.csv',
          'model_outputs/scenario_dcf.csv','model_outputs/sensitivity.csv',
          'model_outputs/terminal_economics.csv','docs/investment_thesis.md',
          'docs/forecast_dcf_methodology.md','docs/valuation_evidence_review.md',
          'docs/q3_2026_ttm_dashboard.md']
URLS = {
 'K':'https://www.sec.gov/Archives/edgar/data/1596532/000159653226000013/anet-20251231.htm',
 'Q':'https://www.sec.gov/Archives/edgar/data/1596532/000159653226000254/anet-20260930.htm',
 'N':'https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm',
 'R1':'https://github.com/ericashieh0308-creator/ANET-Equity-Research/blob/ef5c8b0/docs/forecast_dcf_methodology.md',
 'R2':'https://github.com/ericashieh0308-creator/ANET-Equity-Research/blob/ef5c8b0/docs/valuation_evidence_review.md',
 'R3':'https://github.com/ericashieh0308-creator/ANET-Equity-Research/blob/ef5c8b0/docs/investment_thesis.md',
 'R4':'https://github.com/ericashieh0308-creator/ANET-Equity-Research/blob/ef5c8b0/docs/q3_2026_ttm_dashboard.md'}


def setup_fonts():
    directory = Path('/usr/share/fonts/truetype/dejavu')
    # Embed real Unicode glyphs, including en/em dashes, minus and delta.
    for name, filename in [('Body','DejaVuSans.ttf'),('Bold','DejaVuSans-Bold.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(directory / filename)))
    pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Body',boldItalic='Bold')


def style(size=9.2, leading=12.6, **kwargs):
    options=dict(fontName='Body',fontSize=size,leading=leading,textColor=NAVY,alignment=TA_LEFT,spaceAfter=6)
    options.update(kwargs)
    return ParagraphStyle('report',**options)


def para(text, size=9.2, leading=12.6):
    if isinstance(text,Paragraph):return text
    text=escape(str(text))
    # Every near-claim citation links directly to its registered source.
    import re
    text=re.sub(r'\b(R[1-4]|K|Q|N)\b(?=[,;\]– ])',
                lambda m: '<a href="'+URLS[m[0]]+'" color="#147D85">'+m[0]+'</a>',text)
    return Paragraph(text,style(size,leading))


def table(headers, rows, widths=None, size=8.1):
    header_style=style(size,11,fontName='Bold',textColor=colors.white)
    cells=[[Paragraph(escape(str(x)),header_style) for x in headers]]+[[para(x,size,11) for x in row] for row in rows]
    t=Table(cells,colWidths=widths or [WIDTH/len(headers)]*len(headers),hAlign='LEFT',repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#EFF4F7'),colors.white]),
        ('LINEBELOW',(0,0),(-1,0),0.8,TEAL),('LINEBELOW',(0,-1),(-1,-1),0.4,GRAY),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),
        ('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),4),
        ('BOTTOMPADDING',(0,0),(-1,-1),2)]))
    return t


def f(value):return f'{value:,.1f}'
def pct(value):return f'{value*100:.1f}%'


def chart(labels, first, second, names, title, max_value=None):
    """Vector grouped bars: no raster labels, axes and common zero baseline."""
    d=Drawing(WIDTH,150)
    d.add(String(0,139,title,fontName='Bold',fontSize=9,fillColor=NAVY))
    top=max_value or max(max(first),max(second))*1.14
    left,bottom,w,h=48,28,WIDTH-60,91
    for frac in [0,.5,1]:
        y=bottom+h*frac
        d.add(Line(left,y,left+w,y,strokeColor=colors.HexColor('#DDE5EA'),strokeWidth=.4))
        d.add(String(left-6,y-3,f'{top*frac:,.0f}',fontName='Body',fontSize=7.3,textAnchor='end',fillColor=GRAY))
    gap=w/len(labels)
    for n,label in enumerate(labels):
        x=left+gap*(n+.5)
        for offset,vals,color in [(-15,first,NAVY),(2,second,TEAL)]:
            d.add(Rect(x+offset,bottom,13,h*vals[n]/top,fillColor=color,strokeColor=None))
        d.add(String(x,bottom-12,label,fontName='Body',fontSize=8,textAnchor='middle',fillColor=NAVY))
    for x,name,color in [(55,names[0],NAVY),(260,names[1],TEAL)]:
        d.add(Rect(x,3,7,7,fillColor=color,strokeColor=None))
        d.add(String(x+12,3,name,fontName='Body',fontSize=7.8,fillColor=GRAY))
    return d


def components():
    a=pd.read_csv(ROOT/INPUTS[2]).set_index('fiscal_year')
    q=pd.read_csv(ROOT/INPUTS[3]).set_index('period')
    cfg=json.loads((ROOT/INPUTS[4]).read_text())['scenarios']
    forecasts=pd.read_csv(ROOT/INPUTS[5]);v=pd.read_csv(ROOT/INPUTS[6]).set_index('scenario')
    sensitivity=pd.read_csv(ROOT/INPUTS[7]);term=pd.read_csv(ROOT/INPUTS[8]).set_index('scenario')
    assert v.bridge_status.eq('BLOCKED').all() and v.value_per_share.isna().all()
    c={}
    c['summary']=table(['Evidence / model status','Portfolio finding'],[
      ['Reported historical','FY2023–FY2025 and Q3 / 9M2026 sourced to SEC statements.'],
      ['Derived analysis','Growth, margins, separate analytical FCF measures and additive TTM income.'],
      ['Hypothetical scenarios','Base EV '+f(v.loc['Base','enterprise_value'])+'; Bull '+f(v.loc['Bull','enterprise_value'])+'; Bear '+f(v.loc['Bear','enterprise_value'])+' (USD millions).'],
      ['Unresolved valuation','Equity value and per-share output BLOCKED; no recommendation.']], [135,WIDTH-135])
    c['competition']=table(['Issuer disclosure','Research implication / qualification'],[
      ['Cisco: competing portfolios and bundled solutions. [K, Item 1 pp.8–9]','Test operating simplicity against procurement breadth; no relative price/performance ranking is established.'],
      ['NVIDIA: Ethernet, InfiniBand and NVLink interconnect/switch platforms. [N, Item 1 “Data Center” p.5]','Architecture coverage is not proof of vendor selection. NVIDIA and ANET fiscal years are not aligned for peer financial comparisons.'],
      ['Arista: common software architecture and merchant silicon. [K, Item 1 pp.6–8]','Test retention, costs and pricing against independent customer evidence.']], [200,WIDTH-200])
    metrics=[('Revenue','revenue'),('Gross profit','gross_profit'),('Operating income','operating_income'),('Net income','net_income')]
    c['annual']=table(['USD millions','FY2023','FY2024','FY2025'],[[label]+[f(a.loc[y,key]) for y in [2023,2024,2025]] for label,key in metrics],[155,116,116,WIDTH-387])
    c['annual_chart']=chart(['FY2023','FY2024','FY2025'],a.revenue.tolist(),a.operating_income.tolist(),['Reported revenue','Reported operating income'],'Annual revenue and operating income | USD millions')
    periods=['Q3 2025','Q3 2026','9M 2025','9M 2026']
    c['interim']=table(['USD millions']+periods,[[label]+[f(q.loc[p,key]) for p in periods] for label,key in metrics]+[['Diluted EPS (USD)']+[f'{q.loc[p,"diluted_eps"]:.2f}' for p in periods]],[145]+[(WIDTH-145)/4]*4)
    cash=[]
    for y in [2023,2024,2025]:
        row=a.loc[y];cap=abs(row.property_equipment_intangible_purchases)
        cash.append([f'FY{y}',f(row.operating_cash_flow),'('+f(cap)+')',f(row.operating_cash_flow-cap),'Combined'])
    for p in ['9M 2025','9M 2026']:
        row=q.loc[p];cash.append([p+' YTD',f(row.operating_cash_flow),'('+f(row.ppe_purchases_outflow_magnitude)+')',f(row.analytical_fcf_ppe_only),'PP&E only'])
    c['cash']=table(['Period','Reported OCF','Purchases','Derived FCF','Purchase scope'],cash,[93,100,92,100,WIDTH-385])
    c['cash_chart']=chart(['9M2025 YTD','9M2026 YTD'],[q.loc[p,'operating_cash_flow'] for p in ['9M 2025','9M 2026']],[q.loc[p,'analytical_fcf_ppe_only'] for p in ['9M 2025','9M 2026']],['Reported OCF','Analytical PP&E-only FCF'],'Interim cash generation | USD millions')
    c['hypotheses']=table(['Preliminary hypothesis','Evidence / counterargument'],[
      ['1. AI networking could sustain demand.','Management describes AI/cloud networking demand [K pp.2–3; Q pp.14–15]. Counterargument: acceptance delays, spending reprioritization or competing architectures may limit conversion. Test deployment schedules and repeat purchases.'],
      ['2. Software consistency could support repeat purchasing.','EOS / CloudVision platform descriptions provide a starting point [K pp.1–6]. Counterargument: bundled competition or limited proven cost benefit may weaken differentiation. Test independent customer economics and renewals.'],
      ['3. Scale could support operating leverage.','Historical operating income rose [K p.69; Q p.2]. Counterargument: gross-margin pressure and reinvestment/NWC absorption can offset scale. Test normalized cash conversion, not earnings alone.']], [170,WIDTH-170])
    drivers=[('Q4 FY2026 revenue YoY','q4_2026_revenue_yoy'),('Gross margin','gross_margin'),('OpEx / revenue','opex_ratio'),('Operating tax rate','tax_rate'),('D&A / revenue','da_ratio'),('PP&E / revenue','ppe_capex_ratio'),('Extra intangible budget / revenue','intangible_reinvestment_ratio'),('Year-end NWC / annual revenue','nwc_ratio'),('WACC','wacc'),('Terminal growth','terminal_growth')]
    rows=[[label]+[pct(cfg[s][key]) for s in ['Base','Bull','Bear']] for label,key in drivers]
    rows.insert(1,['FY2027–2030 growth']+[', '.join(f'{x*100:g}%' for x in cfg[s]['growth_2027_2030']) for s in ['Base','Bull','Bear']])
    c['drivers']=table(['Driver','Base','Bull','Bear'],rows,[185]+[(WIDTH-185)/3]*3,size=7.8)
    b=forecasts[forecasts.scenario.eq('Base')].set_index('fiscal_year')
    specs=[('Revenue','revenue'),('Revenue growth','revenue_growth'),('Gross margin','gross_margin'),('Operating expenses','operating_expenses'),('Operating income / EBIT','operating_income'),('Operating margin','operating_margin'),('Modeled taxes','modeled_operating_taxes'),('NOPAT','nopat'),('D&A','da'),('PP&E purchases','ppe_capex'),('Extra intangible budget','hypothetical_intangible_reinvestment'),('Change in NWC proxy','change_nwc'),('Full-year modeled FCFF','annual_fcff'),('DCF-included FCFF','dcf_included_fcff')]
    c['forecast']=table(['USD millions / %']+[f'FY{y}E' for y in b.index],[[label]+[(pct if key in ['revenue_growth','gross_margin','operating_margin'] else f)(b.loc[y,key]) for y in b.index] for label,key in specs],[163]+[(WIDTH-163)/5]*5,size=7.3)
    c['valuation']=table(['Case','WACC','Terminal g','Enterprise value','Terminal PV / EV'],[[s,pct(v.loc[s,'wacc']),pct(v.loc[s,'terminal_growth']),f(v.loc[s,'enterprise_value']),pct(v.loc[s,'terminal_value_share'])] for s in ['Base','Bull','Bear']],[70,75,85,140,WIDTH-370])
    z=sensitivity[sensitivity.scenario.eq('Base')].pivot(index='wacc',columns='terminal_growth',values='enterprise_value')
    c['sensitivity']=table(['WACC / g']+[pct(g) for g in z.columns],[[pct(w)]+[f(z.loc[w,g]) for g in z.columns] for w in z.index],[78]+[(WIDTH-78)/len(z.columns)]*len(z.columns),size=7.8)
    c['terminal']=table(['Case','Net reinvestment / NOPAT','Implied incremental return'],[[s,pct(v.loc[s,'terminal_reinvestment_rate']),pct(v.loc[s,'implied_terminal_incremental_roc'])] for s in ['Base','Bull','Bear']],[85,210,WIDTH-295])
    source_names={'K':'ANET FY2025 Form 10-K: business pp.1–9; risks pp.14–15; statements pp.68–69,72; leases p.86.',
      'Q':'ANET Sep. 2026 Form 10-Q (filed Nov. 4): statements pp.1,2,5; Notes 1–7 pp.6–12; MD&A pp.14–19; risks pp.23–30.',
      'N':'NVIDIA FY2026 Form 10-K: Item 1, Data Center p.5. Product coverage only.',
      'R1':'Forecast and DCF methodology: formulas, assumptions and timing.',
      'R2':'Valuation evidence review: bridge, classification and terminal audit.',
      'R3':'Sourced investment thesis: business, preliminary hypotheses and risks.',
      'R4':'Quarterly / TTM methodology: periods, formula and EPS/FCF limits.'}
    c['sources']=table(['Reference','Source / scope (click to open)'],[[key,Paragraph('<a href="'+url+'" color="#147D85">'+escape(source_names[key])+'</a>',style(8,11))] for key,url in URLS.items()],[65,WIDTH-65],size=8)
    return c


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(TEAL);canvas.setLineWidth(.6);canvas.line(46,807,549,807)
    canvas.setFont('Body',7.2);canvas.setFillColor(GRAY)
    canvas.drawString(46,818,'ANET | EQUITY RESEARCH & SCENARIO-BASED DCF')
    canvas.drawString(46,30,'Ya-Cheng Hsieh (Erica Hsieh) | November 8, 2026 | Portfolio research')
    canvas.drawRightString(549,30,f'{doc.page} / 8')
    canvas.restoreState()


def build():
    setup_fonts();c=components();story=[]
    pages=SOURCE.read_text().split('---PAGE---')
    if len(pages)!=8:raise ValueError('Report must have eight explicit pages.')
    for index,page in enumerate(pages):
        if index:story.append(PageBreak())
        import re
        page=re.sub(r'(?m)^(#{1,3} .+)$',r'\n\1\n',page)
        for block in re.split(r'\n\s*\n',page.strip()):
            block=' '.join(block.splitlines())
            if block.startswith('{{'):
                key=block[2:-2];story.extend([c[key],Spacer(1,10)])
            elif block.startswith('### '):
                story.append(Paragraph(escape(block[4:]),style(10.4,14,fontName='Bold',spaceBefore=6)))
            elif block.startswith('## '):
                story.append(Paragraph(escape(block[3:]),style(14,19,fontName='Bold',spaceBefore=2)))
            elif block.startswith('# '):
                story.append(Paragraph(escape(block[2:]),style(19 if index==0 else 16,24,fontName='Bold',spaceBefore=6)))
            else:story.append(para(block))
    SimpleDocTemplate(str(PDF),pagesize=(595.28,841.89),leftMargin=46,rightMargin=46,
      topMargin=49,bottomMargin=47,title='Arista Networks (NYSE: ANET) — Equity Research & Scenario-Based DCF Valuation',
      author='Ya-Cheng Hsieh (Erica Hsieh)',invariant=1).build(story,onFirstPage=footer,onLaterPages=footer)
    manifest={'research_date':'2026-11-08','main_baseline':'ef5c8b0','source':str(SOURCE.relative_to(ROOT)),
      'pdf':str(PDF.relative_to(ROOT)),'input_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in INPUTS},
      'pdf_sha256':hashlib.sha256(PDF.read_bytes()).hexdigest(),
      'evidence_policy':'Existing repository sources only; all forward cases hypothetical; equity/per-share BLOCKED.'}
    (OUT/'report_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(PDF)

if __name__=='__main__':build()
