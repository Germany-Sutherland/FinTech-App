import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import os

# -------------------------
# How to Use This Web App
# -------------------------
st.title("📊 FinTech Mini Suite — Free & Simple")

st.markdown("""
### How to Use This Web App
1. **Market Data** → Enter a valid ticker (e.g., `AAPL`, `MSFT`, `BTC-USD`, `NIFTYBEES.NS`).
2. **Fallback System**:
    - Tries **Yahoo Finance** first.
    - If Yahoo fails, tries **Finnhub API**.
    - If both fail, shows **sample CSV data** from GitHub repo.
3. Works on **free GitHub + free Streamlit Cloud**.
""")

# -------------------------
# Inputs
# -------------------------
ticker = st.text_input("Ticker Symbol", "AAPL")
period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2)
interval = st.selectbox("Interval", ["1d", "1wk", "1mo"], index=0)

# -------------------------
# Fetch Data Function
# -------------------------
def fetch_data(ticker, period, interval):
    # 1. Try Yahoo Finance
    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False)
        if not data.empty:
            return data, "Yahoo Finance"
    except Exception:
        pass

    # 2. Try Finnhub
    try:
        api_key = st.secrets.get("FINNHUB_API_KEY", None)
        if api_key:
            url = f"https://finnhub.io/api/v1/stock/candle?symbol={ticker}&resolution=D&from=1609459200&to=1672444800&token={api_key}"
            r = requests.get(url)
            if r.status_code == 200:
                js = r.json()
                if "c" in js and js["c"]:
                    df = pd.DataFrame({
                        "Close": js["c"],
                        "Open": js["o"],
                        "High": js["h"],
                        "Low": js["l"]
                    })
                    return df, "Finnhub API"
    except Exception:
        pass

    # 3. Fallback to sample CSV
    try:
        sample_path = os.path.join(os.path.dirname(__file__), "sample_data.csv")
        df = pd.read_csv(sample_path, parse_dates=["Date"], index_col="Date")
        return df, "Sample CSV"
    except Exception:
        pass

    return None, None

# -------------------------
# Main
# -------------------------
if st.button("Get Data"):
    df, source = fetch_data(ticker, period, interval)

    if df is not None:
        st.success(f"Data loaded from **{source}**")
        st.dataframe(df.head())
        st.line_chart(df["Close"])
    else:
        st.error("No data available from any source.")

