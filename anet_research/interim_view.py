"""Separate Streamlit presentation for reviewed interim data and TTM income."""
import pandas as pd
import plotly.express as px
import streamlit as st

from anet_research.interim import (
    VIEW, ANNUAL_URL, EPS_BLOCK, FCF_BLOCK, load_interim, load_ttm_annual, comparisons, ttm_income, yoy,
)
from anet_research.quarterly import DATA, SOURCE_URL, FCF_DEFINITION

NAMES = {'revenue':'Revenue', 'gross_profit':'Gross profit', 'operating_income':'Operating income',
         'net_income':'Net income', 'diluted_eps':'Diluted EPS', 'cost_of_revenue':'Cost of revenue',
         'operating_expenses':'Operating expenses', 'free_cash_flow':'TTM FCF (blocked)'}


def render_interim():
    st.header(VIEW)
    st.caption('Unaudited condensed consolidated statements. USD millions; diluted EPS in USD per share.')
    st.markdown(f'[Official SEC Form 10-Q]({SOURCE_URL}) · Filed November 4, 2026 · '
                'Part I, Item 1: income p.2, balance sheets p.1, cash flows p.5 (filing printed pages).')
    try:
        interim, balance = load_interim()
        comparison = comparisons(interim)
    except (ValueError, OSError, KeyError) as exc:
        st.error(f'Cannot verify interim data: {exc}')
        return
    st.success('Interim CSVs reconcile to the preserved official SEC source; source hashes and arithmetic checked.')
    quarter_tab, ytd_tab = st.tabs(['Q3: three months ended September 30', '9M: nine months ended September 30'])
    for tab, kind in [(quarter_tab,'Quarter (Q3)'), (ytd_tab,'Nine months YTD (9M)')]:
        with tab:
            shown = comparison[comparison.period_type.eq(kind)]
            display = shown[['metric','current_period','prior_period','current_value','prior_value','yoy_growth','units']].copy()
            display['metric'] = display.metric.map(NAMES)
            st.dataframe(display.rename(columns={'yoy_growth':'YoY growth'}).style.format(
                {'current_value':'{:,.2f}','prior_value':'{:,.2f}','YoY growth':'{:.2%}'}, na_rep='—'),
                hide_index=True, width='stretch')
            amounts = shown[shown.metric.ne('diluted_eps')].melt(
                id_vars=['metric'], value_vars=['current_value','prior_value'], var_name='Comparison',value_name='USD millions')
            amounts['Comparison'] = amounts.Comparison.map({'current_value':shown.iloc[0].current_period,
                                                           'prior_value':shown.iloc[0].prior_period})
            amounts['metric'] = amounts.metric.map(NAMES)
            st.plotly_chart(px.bar(amounts,x='metric',y='USD millions',color='Comparison',barmode='group'),width='stretch')
    st.caption('YoY = current / prior − 1, comparing matching durations only. Missing inputs or nonpositive prior values leave growth blank. EPS growth uses rounded reported EPS.')
    st.download_button('Download Q3 and 9M comparisons CSV',comparison.to_csv(index=False),
                       'anet_q3_9m_comparisons.csv','text/csv')

    st.subheader('9M operating cash flow and PP&E-only FCF — year to date')
    st.warning('Cash flows are nine-month YTD amounts. Standalone Q3 operating cash flow, PP&E purchases and FCF are not reported or inferred.')
    cash = interim[interim.duration_months.eq(9)][['period_label','period_start','period_end','duration_months','operating_cash_flow',
        'purchases_of_property_and_equipment_signed','analytical_fcf_ppe_only','fcf_definition','source_url','source_reference','verification_status']].copy()
    cash['operating_cash_flow_yoy'] = yoy(cash.operating_cash_flow.iloc[0], cash.operating_cash_flow.iloc[1])
    cash['fcf_yoy'] = yoy(cash.analytical_fcf_ppe_only.iloc[0], cash.analytical_fcf_ppe_only.iloc[1])
    # Growth pertains to the 2026 comparison only, not the 2025 base observation.
    cash.loc[cash.index[1], ['operating_cash_flow_yoy','fcf_yoy']] = float('nan')
    st.caption(FCF_DEFINITION + ' = operating cash flow − absolute value of reported signed PP&E purchases. Separate from annual FCF including intangibles.')
    st.dataframe(cash.rename(columns={'analytical_fcf_ppe_only':FCF_DEFINITION}).style.format(
        {'operating_cash_flow_yoy':'{:.2%}','fcf_yoy':'{:.2%}'},na_rep='—'),hide_index=True,width='stretch')
    st.download_button('Download 9M cash flow analysis CSV',cash.to_csv(index=False),'anet_9m_cash_flow_analysis.csv','text/csv')

    st.subheader('TTM income — October 1, 2025 through September 30, 2026')
    st.caption('Analytical TTM = FY2025 + 9M2026 − 9M2025. Calculated per metric only from verified, present inputs with matching periods and units. No annualization.')
    try:
        annual = load_ttm_annual()
    except (ValueError, OSError, KeyError) as exc:
        st.warning(f'Annual input verification failed; TTM unavailable: {exc}')
        annual = pd.DataFrame(columns=['fiscal_year'])
    ttm = ttm_income(annual,interim)
    view = ttm[['metric','fy2025','nine_months_2026','nine_months_2025','value','units','status']].copy()
    view['metric'] = view.metric.map(NAMES)
    st.dataframe(view.style.format({c:'{:,.2f}' for c in ['fy2025','nine_months_2026','nine_months_2025','value']},na_rep='—'),
                 hide_index=True,width='stretch')
    st.info(EPS_BLOCK + ' The disclosed 9M EPS must not be summed as quarterly EPS or treated as an additive dollar amount.')
    st.warning('TTM FCF not calculated. ' + FCF_BLOCK)
    st.markdown(f'Annual input: local 2025 Form 10-K PDF p.73 (printed p.69), [SEC filing]({ANNUAL_URL}). '
                f'Interim input: [2026 Form 10-Q]({SOURCE_URL}), printed p.2. '
                'Annual figures were checked against the local PDF; the annual source has not been independently authenticated online.')
    st.download_button('Download TTM income analysis CSV',ttm.to_csv(index=False),'anet_ttm_income.csv','text/csv')
    with st.expander('Source data, balance sheets and provenance'):
        st.caption('The source captures are web-reader text, not raw HTML. Source labels, signs, units, periods, accession and filing pages accompany the statement rows. 2023 balance sheet remains unavailable in the annual PDF.')
        st.dataframe(balance,hide_index=True,width='stretch')
        st.download_button('Download interim metrics and provenance CSV',interim.to_csv(index=False),'anet_interim_metrics.csv','text/csv')
        for statement in ['income_statement','balance_sheet','cash_flow_statement']:
            path = DATA / f'anet_20260930_{statement}.csv'
            st.download_button(f'Download source {statement.replace("_"," ")} CSV',path.read_bytes(),path.name,'text/csv')
