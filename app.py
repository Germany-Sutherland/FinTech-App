import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="💹 FinTech Mini Suite", layout="wide")

st.title("💹 FinTech Mini Suite — Free & Simple")
st.caption("Portfolio tracker • Strategy backtest • ETF allocator • Risk snapshot — built for free Git + free Streamlit")

# Create main tabs
tabs = st.tabs(["Market Data", "Portfolio", "Backtest (SMA)", "ETF Allocator", "Risk (VaR)"])

# ---------- TAB 1: Market Data ----------
with tabs[0]:
    st.subheader("Market Data Explorer")
    ticker = st.text_input("Ticker (e.g., AAPL, MSFT, BTC-USD, NIFTYBEES.NS)", "AAPL")
    period = st.selectbox("Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "ytd", "max"], index=5)
    interval = st.selectbox("Interval", ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1d", "5d", "1wk", "1mo", "3mo"], index=8)

    if ticker:
        data = yf.download(ticker, period=period, interval=interval)
        if not data.empty:
            st.write(data.tail())
            fig = px.line(data, x=data.index, y="Close", title=f"{ticker} Closing Prices")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data found for that ticker.")

# ---------- TAB 2: Portfolio Tracker ----------
with tabs[1]:
    st.subheader("Portfolio Tracker")
    default_portfolio = {"AAPL": 10, "MSFT": 5, "GOOGL": 2}
    portfolio_df = pd.DataFrame({"Ticker": list(default_portfolio.keys()), "Shares": list(default_portfolio.values())})
    portfolio_df = st.data_editor(portfolio_df, num_rows="dynamic", use_container_width=True)

    total_value = 0
    values = []
    for _, row in portfolio_df.iterrows():
        try:
            price = yf.Ticker(row["Ticker"]).history(period="1d")["Close"].iloc[-1]
            val = price * row["Shares"]
            values.append(val)
            total_value += val
        except:
            values.append(0)

    portfolio_df["Value"] = values
    st.write("Portfolio Value: ${:,.2f}".format(total_value))
    st.dataframe(portfolio_df)

# ---------- TAB 3: Simple Moving Average Backtest ----------
with tabs[2]:
    st.subheader("SMA Backtest")
    ticker_bt = st.text_input("Ticker for backtest", "AAPL")
    sma_short = st.number_input("Short SMA window", min_value=5, max_value=50, value=20)
    sma_long = st.number_input("Long SMA window", min_value=10, max_value=200, value=50)

    if ticker_bt:
        data_bt = yf.download(ticker_bt, period="1y", interval="1d")
        if not data_bt.empty:
            data_bt["SMA_Short"] = data_bt["Close"].rolling(window=sma_short).mean()
            data_bt["SMA_Long"] = data_bt["Close"].rolling(window=sma_long).mean()
            fig_bt = px.line(data_bt, x=data_bt.index, y=["Close", "SMA_Short", "SMA_Long"],
                             title=f"{ticker_bt} SMA Backtest")
            st.plotly_chart(fig_bt, use_container_width=True)

# ---------- TAB 4: ETF Allocator ----------
with tabs[3]:
    st.subheader("ETF Allocator")
    default_etfs = {"SPY": 50, "AGG": 30, "GLD": 20}
    etf_rows = st.data_editor(
        pd.DataFrame({"Ticker": list(default_etfs.keys()), "TargetWeight": list(default_etfs.values())}),
        num_rows="dynamic",
        use_container_width=True,
        key="etfs_editor"
    )
    st.write("Your ETF Allocation Plan")
    st.dataframe(etf_rows)

# ---------- TAB 5: Value at Risk ----------
with tabs[4]:
    st.subheader("Risk Snapshot (Historical VaR)")
    ticker_risk = st.text_input("Ticker for risk analysis", "AAPL")
    confidence = st.slider("Confidence Level", 90, 99, 95)

    if ticker_risk:
        data_risk = yf.download(ticker_risk, period="1y", interval="1d")
        if not data_risk.empty:
            returns = data_risk["Close"].pct_change().dropna()
            var = np.percentile(returns, 100 - confidence)
            st.write(f"{confidence}% 1-day Historical VaR: {var*100:.2f}%")
