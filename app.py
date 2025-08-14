import streamlit as st
import yfinance as yf
import plotly.express as px
import pandas as pd
import numpy as np

# -------------------------------
# HOW TO USE THIS WEB APP
# -------------------------------
st.title("💹 FinTech Mini Suite — Free & Simple")
st.markdown("""
**Welcome!** This free FinTech app runs entirely on open-source tools and free APIs.  
You can use it to **explore stocks, track portfolios, backtest simple strategies, allocate ETFs, and view basic risk metrics**.

**How to use:**
1. **Market Data Tab** → Type a ticker (e.g., `AAPL`, `MSFT`, `BTC-USD`) and choose a period/interval to view recent closing prices.
2. **Portfolio Tab** → Enter your tickers and quantities to calculate your portfolio's current value.
3. **Backtest Tab** → Test a simple **SMA crossover strategy** for any ticker to see buy/sell points.
4. **ETF Allocator Tab** → Enter ETFs and expected returns; app suggests equal-weight allocation.
5. **Risk Tab** → View simple **Value-at-Risk (VaR)** metrics using historical simulation.

**Tips:**
- This app uses free `yfinance` data — if data is missing, try a different period/interval.
- Keep inputs short to stay within Streamlit free tier limits.
- No sign-in, no cost — runs entirely on free GitHub + free Streamlit Cloud.

---
""")

# Tabs
tabs = st.tabs(["Market Data", "Portfolio", "Backtest (SMA)", "ETF Allocator", "Risk (VaR)"])

# ---------- TAB 1: Market Data ----------
with tabs[0]:
    st.subheader("Market Data Explorer")
    ticker = st.text_input("Ticker (e.g., AAPL, MSFT, BTC-USD, NIFTYBEES.NS)", "AAPL")
    period = st.selectbox("Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "ytd", "max"], index=5)
    interval = st.selectbox("Interval", ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1d", "5d", "1wk", "1mo", "3mo"], index=8)

    if ticker:
        data = yf.download(ticker, period=period, interval=interval)

        if data.empty:
            st.warning("No data returned for that ticker/period. Try changing settings.")
        elif "Close" not in data.columns or data["Close"].dropna().empty:
            st.warning("No valid 'Close' price data found for plotting.")
            st.write(data.tail())
        else:
            st.write(data.tail())
            fig = px.line(
                data.dropna(subset=["Close"]),
                x=data.index,
                y="Close",
                title=f"{ticker} Closing Prices"
            )
            st.plotly_chart(fig, use_container_width=True)

# ---------- TAB 2: Portfolio Tracker ----------
with tabs[1]:
    st.subheader("Portfolio Tracker")
    tickers_input = st.text_area("Enter tickers (comma separated)", "AAPL,MSFT,GOOGL")
    qty_input = st.text_area("Enter quantities (comma separated)", "10,5,8")

    if st.button("Calculate Portfolio Value"):
        tickers_list = [t.strip() for t in tickers_input.split(",")]
        qty_list = [float(q) for q in qty_input.split(",")]

        prices = yf.download(tickers_list, period="1d")["Close"].iloc[-1]
        df_portfolio = pd.DataFrame({
            "Ticker": tickers_list,
            "Quantity": qty_list,
            "Last Price": [prices[t] for t in tickers_list],
        })
        df_portfolio["Total Value"] = df_portfolio["Quantity"] * df_portfolio["Last Price"]

        st.dataframe(df_portfolio)
        st.success(f"Portfolio Total Value: ${df_portfolio['Total Value'].sum():,.2f}")

# ---------- TAB 3: SMA Backtest ----------
with tabs[2]:
    st.subheader("Simple SMA Backtest")
    ticker_bt = st.text_input("Ticker for backtest", "AAPL")
    short_window = st.slider("Short SMA window", 5, 50, 20)
    long_window = st.slider("Long SMA window", 20, 200, 50)

    if st.button("Run Backtest"):
        data_bt = yf.download(ticker_bt, period="1y", interval="1d")
        if not data_bt.empty:
            data_bt["SMA_short"] = data_bt["Close"].rolling(short_window).mean()
            data_bt["SMA_long"] = data_bt["Close"].rolling(long_window).mean()
            fig_bt = px.line(data_bt, x=data_bt.index, y=["Close", "SMA_short", "SMA_long"], title=f"{ticker_bt} SMA Backtest")
            st.plotly_chart(fig_bt, use_container_width=True)
        else:
            st.warning("No data for backtest.")

# ---------- TAB 4: ETF Allocator ----------
with tabs[3]:
    st.subheader("ETF Allocator")
    etf_input = st.text_area("Enter ETF tickers (comma separated)", "SPY,IVV,VOO")
    exp_return_input = st.text_area("Enter expected returns (comma separated, in %)", "8,7,9")

    if st.button("Allocate ETFs"):
        etfs = [e.strip() for e in etf_input.split(",")]
        returns = [float(r) for r in exp_return_input.split(",")]
        allocation = [1/len(etfs)] * len(etfs)  # Equal weight
        df_etf = pd.DataFrame({
            "ETF": etfs,
            "Expected Return (%)": returns,
            "Allocation (%)": [a*100 for a in allocation]
        })
        st.dataframe(df_etf)

# ---------- TAB 5: Risk Metrics ----------
with tabs[4]:
    st.subheader("Risk (Value-at-Risk)")
    ticker_risk = st.text_input("Ticker for risk analysis", "AAPL")
    confidence = st.slider("Confidence Level", 90, 99, 95)

    if st.button("Calculate VaR"):
        data_risk = yf.download(ticker_risk, period="1y")["Close"].pct_change().dropna()
        if not data_risk.empty:
            var = np.percentile(data_risk, 100 - confidence)
            st.write(f"{confidence}% 1-day VaR: {var*100:.2f}%")
        else:
            st.warning("No data for risk calculation.")
