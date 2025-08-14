# Updated streamlit_app.py — replaced st.experimental_data_editor with st.data_editor to work with latest Streamlit

# ... previous imports and setup remain unchanged ...

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

    etf_rows = st.data_editor(
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

# ... rest of the code remains unchanged ...
