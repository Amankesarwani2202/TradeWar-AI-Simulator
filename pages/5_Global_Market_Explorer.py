import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(page_title='Global Market Explorer', page_icon='🌐', layout='wide')

MARKETS = {
    'India': [('NIFTY 50','^NSEI'),('NIFTY Bank','^NSEBANK'),('BSE Sensex','^BSESN'),('NIFTY IT','^CNXIT'),('NIFTY Midcap 100','^CNXMC'),('NIFTY Smallcap 100','^CNXSC')],
    'China': [('SSE Composite','000001.SS'),('CSI 300','000300.SS'),('Shenzhen Component','399001.SZ'),('Hang Seng China Enterprises','^HSCE')],
    'US': [('S&P 500','^GSPC'),('Nasdaq 100','^NDX'),('Dow Jones','^DJI'),('Russell 2000','^RUT'),('VIX','^VIX')],
    'Japan': [('Nikkei 225','^N225'),('TOPIX','^TOPX')],
    'South Korea': [('KOSPI','^KS11'),('KOSDAQ','^KQ11')],
    'Taiwan': [('TAIEX','^TWII')],
    'Vietnam': [('VN-Index','^VNINDEX')],
    'Thailand': [('SET Index','^SET.BK')],
    'EU': [('Euro Stoxx 50','^STOXX50E'),('DAX','^GDAXI'),('CAC 40','^FCHI'),('FTSE 100','^FTSE')],
    'Bangladesh': [('DSEX','DSEX.BD')],
}

st.title('🌐 Global Financial Market Explorer')
st.caption('Explore multiple major indices for each supported economy instead of being limited to one headline index. Data is fetched live through Yahoo Finance when the ticker is available.')

country = st.selectbox('Country / market', list(MARKETS))
choices = MARKETS[country]
selected = st.multiselect('Markets to compare', choices, default=[choices[0]], format_func=lambda x: f'{x[0]} ({x[1]})')
period = st.selectbox('History', ['1mo','3mo','6mo','1y','2y'], index=2)

if not selected:
    st.info('Select at least one market.')
    st.stop()

rows=[]; charts=[]
for label,ticker in selected:
    try:
        data=yf.download(ticker,period=period,progress=False,auto_adjust=True)
        if data.empty: continue
        close=data['Close'].squeeze().dropna()
        last=float(close.iloc[-1]); prev=float(close.iloc[-2]) if len(close)>1 else last
        start=float(close.iloc[0])
        rows.append({'Market':label,'Ticker':ticker,'Latest':round(last,2),'Daily %':round((last/prev-1)*100,2),'Period %':round((last/start-1)*100,2),'Observations':len(close)})
        charts.append((label,close))
    except Exception as exc:
        st.warning(f'{label} ({ticker}) could not be loaded: {exc}')

if rows:
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    for label,close in charts:
        chart=close.rename(label).to_frame()
        st.line_chart(chart,use_container_width=True)
else:
    st.error('No selected ticker returned data. Try another market or period.')

st.divider()
st.subheader('Any Yahoo Finance instrument')
custom=st.text_input('Enter a ticker',placeholder='Example: RELIANCE.NS, TCS.NS, AAPL, MSFT, 0700.HK')
if custom:
    try:
        data=yf.download(custom.strip(),period=period,progress=False,auto_adjust=True)
        if data.empty: st.warning('No data found for this ticker.')
        else:
            close=data['Close'].squeeze().dropna()
            last=float(close.iloc[-1]); prev=float(close.iloc[-2]) if len(close)>1 else last
            st.metric('Latest close',f'{last:,.2f}',f'{(last/prev-1)*100:+.2f}%')
            st.line_chart(close,use_container_width=True)
    except Exception as exc:
        st.error(f'Could not load {custom}: {exc}')
