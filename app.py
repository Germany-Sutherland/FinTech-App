# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
from io import StringIO

# Optional imports guarded so the app still loads even if a lib is missing at first run
try:
    import yfinance as yf
except Exception as e:
    yf = None

try:
    import plotly.express as px
except Exception:
    px = None

st.set_page_config(page_title="FinTech Mini Suite", page_icon="💹", layout="wide")

# -----------------------------
# Helpers & Caching
# -----------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_history(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    if yf is None:
        raise RuntimeError("yfinance not installed. Please add it to requirements.txt")
    data = yf.download(ticker, period=period, interval=interval, auto_adjust=True, progress=False)
    if data is None or data.empty:
        return pd.DataFrame()
    data = data.rename(columns=str.title)
    return data

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_last_price(tickers: list[str]) -> pd.DataFrame:
    if yf is None:
        raise RuntimeError("yfinance not installed. Please add it to requirements.txt")
    if not tickers:
        return pd.DataFrame()
    t = yf.Tickers(" ".join(tickers))
    info = []
    for key, tk in t.tickers.items():
        try:
            p = tk.history(period="1d")
            if not p.empty:
                last = float(p["Close"].iloc[-1])
                info.append({"Ticker": key.upper(), "Price": last})
        except Exception:
            pass
    return pd.DataFrame(info)

# Finance utilities

def max_drawdown(series: pd.Series) -> float:
    if series.empty:
        return np.nan
    cummax = series.cummax()
    drawdown = series/cummax - 1.0
    return float(drawdown.min())


def CAGR(equity_curve: pd.Series, periods_per_year: int) -> float:
    if equity_curve.empty:
        return np.nan
    total_return = equity_curve.iloc[-1] / equity_curve.iloc[0] - 1
    n_periods = len(equity_curve)
    yrs = n_periods / periods_per_year
    if yrs <= 0:
        return np.nan
    return float((1 + total_return) ** (1/yrs) - 1)


def sharpe(returns: pd.Series, risk_free: float = 0.0, periods_per_year: int = 252) -> float:
    if returns.empty:
        return np.nan
    excess = returns - risk_free/periods_per_year
    mu = excess.mean() * periods_per_year
    sigma = excess.std(ddof=1) * np.sqrt(periods_per_year)
    if sigma == 0 or np.isnan(sigma):
        return np.nan
    return float(mu / sigma)


def var_historical(returns: pd.Series, level: float = 0.95) -> float:
    if returns.empty:
        return np.nan
    return float(np.percentile(returns.dropna(), (1 - level) * 100))

# -----------------------------
# UI
# -----------------------------
st.title("💹 FinTech Mini Suite — Free & Simple")
st.caption("Portfolio tracker • Strategy backtest • ETF allocator • Risk snapshot — built for free Git + free Streamlit")

with st.sidebar:
    st.header("Settings")
    st.write("This app uses free, public data via yfinance. Keep tickers reasonable to stay within Streamlit Community limits.")
    st.link_button("Source & README", "https://example.com", help="Replace with your Git repo URL after you push.")

# Tabs
tabs = st.tabs(["Market Data", "Portfolio", "Backtest (SMA)", "ETF Allocator", "Risk (VaR)"])

# -----------------------------
# Tab 1: Market Data
# -----------------------------
with tabs[0]:
    st.subheader("Market Data Explorer")
    col1, col2, col3 = st.columns([2,1,1])
    ticker = col1.text_input("Ticker (e.g., AAPL, MSFT, BTC-USD, NIFTYBEES.NS)", value="AAPL").strip().upper()
    period = col2.selectbox("Period", ["1mo","3mo","6mo","1y","2y","5y","10y","max"], index=3)
    interval = col3.selectbox("Interval", ["1d","1wk","1mo"], index=0)

    if st.button("Load Data", type="primary"):
        try:
            df = fetch_history(ticker, period=period, interval=interval)
            if df.empty:
                st.warning("No data returned. Try another ticker or period.")
            else:
                st.dataframe(df.tail(10))
                # Indicators
                df["SMA20"] = df["Close"].rolling(20).mean()
                df["SMA50"] = df["Close"].rolling(50).mean()
                if px:
                    fig = px.line(df.reset_index(), x=df.reset_index().columns[0], y=["Close","SMA20","SMA50"], title=f"{ticker} Price & SMAs")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.line_chart(df[["Close","SMA20","SMA50"]])
        except Exception as e:
            st.error(f"Error: {e}")

# -----------------------------
# Tab 2: Portfolio
# -----------------------------
with tabs[1]:
    st.subheader("Portfolio Tracker (CSV upload or manual)")
    st.markdown("CSV columns: **Ticker, Shares, CostBasis**. Sample provided in README.")

    sample = st.toggle("Use sample portfolio", value=True)
    uploaded = st.file_uploader("Upload CSV", type=["csv"])

    if sample and uploaded is None:
        csv = """Ticker,Shares,CostBasis\nAAPL,10,150\nMSFT,5,300\nGOOGL,4,120\nBTC-USD,0.02,40000\nNIFTYBEES.NS,50,220\n"""
        pf = pd.read_csv(StringIO(csv))
    elif uploaded is not None:
        pf = pd.read_csv(uploaded)
    else:
        st.info("Upload a CSV or toggle sample.")
        pf = pd.DataFrame()

    if not pf.empty:
        pf["Ticker"] = pf["Ticker"].astype(str).str.upper()
        prices = fetch_last_price(pf["Ticker"].tolist())
        if prices.empty:
            st.warning("Could not fetch prices.")
        else:
            df = pf.merge(prices, on="Ticker", how="left")
            df["MarketValue"] = df["Shares"] * df["Price"]
            df["Cost"] = df["Shares"] * df["CostBasis"]
            df["P/L"] = df["MarketValue"] - df["Cost"]
            df["Return %"] = np.where(df["Cost"]>0, 100*df["P/L"]/df["Cost"], np.nan)
            st.dataframe(df)

            total_mv = float(df["MarketValue"].sum())
            total_cost = float(df["Cost"].sum())
            total_pl = float(df["P/L"].sum())
            colA, colB, colC = st.columns(3)
            colA.metric("Market Value", f"{total_mv:,.2f}")
            colB.metric("Total P/L", f"{total_pl:,.2f}", delta=f"{(100*(total_mv/total_cost-1)) if total_cost>0 else 0:.2f}%")
            colC.metric("Positions", f"{len(df)}")

            if px and not df.empty:
                alloc = df[["Ticker","MarketValue"]].copy()
                alloc = alloc.sort_values("MarketValue", ascending=False)
                fig = px.pie(alloc, names="Ticker", values="MarketValue", title="Allocation by Market Value")
                st.plotly_chart(fig, use_container_width=True)

            # Download
            out = df.copy()
            out_csv = out.to_csv(index=False).encode("utf-8")
            st.download_button("Download enriched portfolio CSV", out_csv, file_name="portfolio_valued.csv", mime="text/csv")

# -----------------------------
# Tab 3: Backtest (SMA Crossover)
# -----------------------------
with tabs[2]:
    st.subheader("SMA Crossover Backtest")
    col1, col2, col3, col4 = st.columns([2,1,1,1])
    bt_ticker = col1.text_input("Ticker", value="AAPL").strip().upper()
    fast = col2.number_input("Fast SMA", value=20, min_value=2, max_value=200, step=1)
    slow = col3.number_input("Slow SMA", value=50, min_value=5, max_value=400, step=1)
    bt_period = col4.selectbox("Period", ["1y","2y","5y","10y","max"], index=2)

    if st.button("Run Backtest", type="primary"):
        if fast >= slow:
            st.warning("Fast SMA should be less than Slow SMA.")
        else:
            data = fetch_history(bt_ticker, period=bt_period, interval="1d")
            if data.empty:
                st.warning("No data.")
            else:
                px_close = data["Close"].dropna()
                sma_f = px_close.rolling(int(fast)).mean()
                sma_s = px_close.rolling(int(slow)).mean()
                signal = (sma_f > sma_s).astype(int)
                signal = signal.shift(1).fillna(0)  # trade next day open/close proxy
                strat_equity = (1 + (px_close.pct_change().fillna(0) * signal)).cumprod()
                bh_equity = (1 + px_close.pct_change().fillna(0)).cumprod()

                # Metrics
                mdd_strat = max_drawdown(strat_equity)
                mdd_bh = max_drawdown(bh_equity)
                cagr_strat = CAGR(strat_equity, periods_per_year=252)
                cagr_bh = CAGR(bh_equity, periods_per_year=252)
                sr_strat = sharpe(px_close.pct_change().fillna(0) * signal)
                sr_bh = sharpe(px_close.pct_change().fillna(0))

                c1, c2, c3 = st.columns(3)
                c1.metric("CAGR (Strat)", f"{cagr_strat*100:,.2f}%")
                c2.metric("Max DD (Strat)", f"{mdd_strat*100:,.2f}%")
                c3.metric("Sharpe (Strat)", f"{sr_strat:,.2f}")
                d1, d2, d3 = st.columns(3)
                d1.metric("CAGR (Buy&Hold)", f"{cagr_bh*100:,.2f}%")
                d2.metric("Max DD (B&H)", f"{mdd_bh*100:,.2f}%")
                d3.metric("Sharpe (B&H)", f"{sr_bh:,.2f}")

                plot_df = pd.DataFrame({"Strategy": strat_equity, "Buy&Hold": bh_equity})
                if px:
                    fig = px.line(plot_df, title=f"Equity Curves — {bt_ticker} ({fast}/{slow} SMA)")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.line_chart(plot_df)

# -----------------------------
# Tab 4: ETF Allocator
# -----------------------------
with tabs[3]:
    st.subheader("ETF Budget Allocator")
    st.markdown("Enter your budget and target weights. The tool buys whole shares and leaves some cash unallocated.")

    budget = st.number_input("Budget (your currency)", min_value=0.0, value=10000.0, step=100.0)
    default_etfs = {
        "VTI": 0.6,  # US Total Market
        "VXUS": 0.3, # Intl ex-US
        "BND": 0.1   # US Bonds
    }
    st.markdown("Default ETFs: VTI 60%, VXUS 30%, BND 10% — edit below")

    etf_rows = st.experimental_data_editor(
        pd.DataFrame({"Ticker": list(default_etfs.keys()), "TargetWeight": list(default_etfs.values())}),
        num_rows="dynamic",
        use_container_width=True,
        key="etfs_editor"
    )

    if st.button("Allocate", type="primary"):
        etf_rows["Ticker"] = etf_rows["Ticker"].astype(str).str.upper()
        if abs(etf_rows["TargetWeight"].sum() - 1.0) > 1e-6:
            st.warning("Target weights must sum to 1.0")
        else:
            prices = fetch_last_price(etf_rows["Ticker"].tolist())
            if prices.empty:
                st.warning("Could not fetch prices.")
            else:
                plan = etf_rows.merge(prices, on="Ticker", how="left")
                plan["TargetAmt"] = plan["TargetWeight"] * budget
                plan["Shares"] = np.floor(plan["TargetAmt"] / plan["Price"]).astype(int)
                plan["InvestAmt"] = plan["Shares"] * plan["Price"]
                cash_left = float(budget - plan["InvestAmt"].sum())
                st.dataframe(plan[["Ticker","Price","TargetWeight","Shares","InvestAmt"]])
                st.metric("Unallocated Cash", f"{cash_left:,.2f}")
                csv = plan.to_csv(index=False).encode("utf-8")
                st.download_button("Download allocation plan", csv, file_name="etf_allocation.csv", mime="text/csv")

# -----------------------------
# Tab 5: Risk (Historical VaR)
# -----------------------------
with tabs[4]:
    st.subheader("Historical VaR (Simple)")
    r_ticker = st.text_input("Ticker for Risk (e.g., AAPL, BTC-USD)", value="AAPL").strip().upper()
    level = st.slider("Confidence Level", min_value=0.80, max_value=0.99, step=0.01, value=0.95)
    r_period = st.selectbox("Period", ["6mo","1y","2y","5y"], index=1)

    if st.button("Compute VaR"):
        data = fetch_history(r_ticker, period=r_period, interval="1d")
        if data.empty:
            st.warning("No data.")
        else:
            rets = data["Close"].pct_change().dropna()
            v = var_historical(rets, level=level)
            st.write(f"**1-day VaR at {int(level*100)}% confidence:** {v*100:.2f}% (historical method)")
            st.caption("Interpretation: On a typical day, you should expect to lose no more than this percentage with the given confidence, based on historical returns.")

# -----------------------------
# Footer
# -----------------------------
st.divider()
st.markdown(
    """
**Notes**
- Data is fetched from Yahoo Finance via `yfinance` (free).
- This is an educational demo. Not investment advice.
- Keep usage light to stay within free Streamlit Community resource limits.
    """
)

# End of file

# -----------------------------
# requirements.txt
# -----------------------------
# Place this in a separate file named requirements.txt at the repo root
# streamlit
# yfinance
# pandas
# numpy
# plotly

# -----------------------------
# README.md
# -----------------------------
# Put the following into README.md in your repo

"""
# 💹 FinTech Mini Suite (Free Streamlit)

A lightweight, free-to-run Streamlit app with:
- Market data explorer (prices + SMAs)
- Portfolio tracker (CSV in → valuation & allocation)
- SMA crossover backtest (vs buy & hold)
- ETF budget allocator (whole-share plan)
- Simple historical VaR risk snapshot

## ▶️ Quickstart (Local)
```bash
python -m venv .venv && source .venv/bin/activate  # on Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## ☁️ Deploy on Streamlit Community Cloud (Free)
1. Push this repo to **GitHub**.
2. Go to https://streamlit.io/cloud and create a new app:
   - Repo: `your-username/your-repo`
   - Main file: `streamlit_app.py`
   - Python version: leave default or 3.11
   - Add `requirements.txt` from this repo
3. Click **Deploy**. Done!

## 📄 Portfolio CSV Format
```
Ticker,Shares,CostBasis
AAPL,10,150
MSFT,5,300
GOOGL,4,120
BTC-USD,0.02,40000
NIFTYBEES.NS,50,220
```

## ❓ FAQ
- **Will it run on the free tier?** Yes — it uses lightweight libs and caches data.
- **No prices / errors?** Some tickers or intervals may have limited data. Try a different one.
- **Can I add crypto?** Yes, e.g. `BTC-USD`, `ETH-USD` via Yahoo Finance.
- **How do I change default ETFs?** Edit the ETF table in the app or change `default_etfs` in code.

## ⚠️ Disclaimer
Educational use only. Not investment advice.
"""
