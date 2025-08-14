import streamlit as st
import yfinance as yf
import plotly.express as px
import pandas as pd
import numpy as np

# ------------------------------
# APP HEADER + USAGE GUIDE
# ------------------------------
st.set_page_config(page_title="FinTech Mini Suite", layout="wide")
st.title("💹 FinTech Mini Suite — Free & Simple")
st.caption("Portfolio tracker • Strategy backtest • ETF allocator • Risk snapshot — built for free Git + free Streamlit")

st.markdown("""
### 📘 How to Use This Web App
1. **Market Data** → Enter a valid ticker (e.g., `AAPL`, `MSFT`, `BTC-USD`, `NIFTYBEES.NS`) and select a period & interval.
2. **Portfolio** → Upload a CSV of tickers & quantities to track live values.
3. **Backtest (SMA)** → Test a simple moving average crossover strategy.
4. **ETF Allocator** → Input ETF tickers & weights, see allocation breakdown.
5. **Risk (VaR)** → Upload portfolio data to compute Value-at-Risk.
6. All features **use free Yahoo Finance** data via `yfinance`.
7. Keep requests small — free Streamlit Cloud has rate limits.
8. If you see "No data returned", try smaller period/interval.
9. Works best with daily or weekly intervals for longer periods.
10. You can use this app as a **resume project** to showcase FinTech + Python skills.
""")

# ------------------------------
# TABS
# ------------------------------
tabs = st.tabs(["Market Data", "Portfolio", "Backtest (SMA)", "ETF Allocator", "Risk (VaR)"])

# ------------------------------
# TAB 1: MARKET DATA
# ------------------------------
with tabs[0]:
    st.subheader("📊 Market Data Explorer")
    ticker = st.text_input("Ticker (e.g., AAPL, MSFT, BTC-USD, NIFTYBEES.NS)", "AAPL")
    period = st.selectbox("Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "5y", "10y", "ytd", "max"], index=4)
    interval = st.selectbox("Interval", ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1d", "5d", "1wk", "1mo", "3mo"], index=8)

    try:
        data = yf.download(ticker, period=period, interval=interval)
        if data.empty:
            st.error("No data returned. Try another ticker or adjust period/interval.")
        elif "Close" not in data.columns:
            st.error("The 'Close' price data is missing for this selection.")
        else:
            data = data.dropna(subset=["Close"])
            fig = px.line(data, x=data.index, y="Close", title=f"{ticker} Closing Prices")
            st.plotly_chart(fig)
            st.dataframe(data)
    except Exception as e:
        st.error(f"Error fetching data: {e}")

# ------------------------------
# TAB 2: PORTFOLIO
# ------------------------------
with tabs[1]:
    st.subheader("📂 Portfolio Tracker")
    uploaded_file = st.file_uploader("Upload CSV with columns: Ticker, Quantity", type="csv")
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            prices = {}
            for t in df["Ticker"]:
                hist = yf.download(t, period="1d", interval="1d")
                if not hist.empty and "Close" in hist.columns:
                    prices[t] = hist["Close"].iloc[-1]
                else:
                    prices[t] = np.nan
            df["Price"] = df["Ticker"].map(prices)
            df["Value"] = df["Quantity"] * df["Price"]
            st.dataframe(df)
            st.metric("Total Portfolio Value", f"${df['Value'].sum():,.2f}")
        except Exception as e:
            st.error(f"Error processing portfolio: {e}")

# ------------------------------
# TAB 3: BACKTEST SMA
# ------------------------------
with tabs[2]:
    st.subheader("📈 Backtest SMA Strategy")
    bt_ticker = st.text_input("Backtest Ticker", "AAPL")
    short_window = st.number_input("Short SMA window", 5, 50, 20)
    long_window = st.number_input("Long SMA window", 10, 200, 50)
    try:
        bt_data = yf.download(bt_ticker, period="1y", interval="1d")
        if bt_data.empty or "Close" not in bt_data.columns:
            st.error("No price data available for backtest.")
        else:
            bt_data["SMA_short"] = bt_data["Close"].rolling(short_window).mean()
            bt_data["SMA_long"] = bt_data["Close"].rolling(long_window).mean()
            fig = px.line(bt_data, x=bt_data.index, y=["Close", "SMA_short", "SMA_long"], title=f"{bt_ticker} SMA Backtest")
            st.plotly_chart(fig)
    except Exception as e:
        st.error(f"Error in backtest: {e}")

# ------------------------------
# TAB 4: ETF ALLOCATOR
# ------------------------------
with tabs[3]:
    st.subheader("📊 ETF Allocator")
    etf_input = st.text_area("Enter ETF tickers and weights (e.g., SPY,50; QQQ,30; IWM,20)", "SPY,50; QQQ,30; IWM,20")
    try:
        parts = [p.strip() for p in etf_input.split(";") if p.strip()]
        etfs, weights = zip(*[(p.split(",")[0], float(p.split(",")[1])) for p in parts])
        alloc_df = pd.DataFrame({"ETF": etfs, "Weight": weights})
        fig = px.pie(alloc_df, values="Weight", names="ETF", title="ETF Allocation")
        st.plotly_chart(fig)
        st.dataframe(alloc_df)
    except Exception as e:
        st.error(f"Error processing ETF allocation: {e}")

# ------------------------------
# TAB 5: RISK (VaR)
# ------------------------------
with tabs[4]:
    st.subheader("⚠ Risk Analysis (VaR)")
    risk_file = st.file_uploader("Upload CSV with historical prices for portfolio", type="csv")
    if risk_file:
        try:
            prices_df = pd.read_csv(risk_file, index_col=0, parse_dates=True)
            returns = prices_df.pct_change().dropna()
            var_95 = np.percentile(returns, 5)  # 5th percentile
            st.write(f"Portfolio 95% daily Value-at-Risk: {var_95:.2%}")
        except Exception as e:
            st.error(f"Error computing VaR: {e}")
