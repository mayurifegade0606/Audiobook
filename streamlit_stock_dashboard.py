# streamlit_stock_dashboard.py
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Stock Analysis Dashboard")

def get_data(ticker, period, interval):
    return yf.download(tickers=ticker, period=period, interval=interval, progress=False)

def sma(series, window):
    return series.rolling(window).mean()

def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def bollinger_bands(series, window=20, n_std=2):
    ma = sma(series, window)
    std = series.rolling(window).std()
    upper = ma + n_std * std
    lower = ma - n_std * std
    return ma, upper, lower

def rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(com=period-1, adjust=True).mean()
    ma_down = down.ewm(com=period-1, adjust=True).mean()
    rs = ma_up / ma_down
    return 100 - (100 / (1 + rs))

st.title("Stock Analysis Dashboard")
col1, col2 = st.columns([1,3])

with col1:
    ticker = st.text_input("Ticker", value="AAPL")
    period = st.selectbox("Period", ["1mo","3mo","6mo","1y","2y","5y","10y"], index=3)
    interval = st.selectbox("Interval", ["1d","1wk","1mo","60m"], index=0)
    sma_window = st.number_input("SMA window", min_value=5, max_value=200, value=20)
    ema_span = st.number_input("EMA span", min_value=5, max_value=200, value=50)
    bb_window = st.number_input("BB window", min_value=10, max_value=100, value=20)
    st.markdown("---")
    if st.button("Fetch data"):
        st.session_state.fetch = True

if 'fetch' not in st.session_state:
    st.session_state.fetch = False

if st.session_state.fetch:
    st.info(f"Fetching {ticker}...")
    df = get_data(ticker, period, interval)
    if df.empty:
        st.error("No data returned. Check ticker/period/interval.")
    else:
        df.dropna(inplace=True)
        df['SMA'] = sma(df['Close'], sma_window)
        df['EMA'] = ema(df['Close'], ema_span)
        ma, upper, lower = bollinger_bands(df['Close'], window=bb_window)
        df['BB_MID'] = ma
        df['BB_UP'] = upper
        df['BB_LOW'] = lower
        df['RSI'] = rsi(df['Close'])

        # Plot
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA'], name=f"SMA{int(sma_window)}", line=dict(width=1)))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA'], name=f"EMA{int(ema_span)}", line=dict(width=1)))
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_UP'], name="BB Upper", line=dict(width=1), opacity=0.5))
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_LOW'], name="BB Lower", line=dict(width=0.5), opacity=0.5))
        fig.update_layout(title=f"{ticker} Price chart", xaxis_rangeslider_visible=False, height=600)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("RSI")
        r_fig = go.Figure()
        r_fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI"))
        r_fig.add_hline(y=70, line_dash="dash", line_color="red")
        r_fig.add_hline(y=30, line_dash="dash", line_color="green")
        r_fig.update_layout(height=250)
        st.plotly_chart(r_fig, use_container_width=True)

        # Data table and CSV download
        st.subheader("Data")
        st.dataframe(df.tail(100))
        csv = df.to_csv().encode('utf-8')
        st.download_button("Download CSV", data=csv, file_name=f"{ticker}_data.csv", mime="text/csv")
