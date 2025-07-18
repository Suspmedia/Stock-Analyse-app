import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from stock_engine import get_stock_price_data
from option_chain import get_oi_levels
from telegram_alert import send_telegram_message
from stock_list import get_top_fo_stocks

from io import BytesIO

st.set_page_config(page_title="📈 Stock Option Analyzer", layout="wide")
st.title("📈 Stock Option Analyzer App")

# Sidebar Inputs
st.sidebar.header("🔍 Configuration")
stock_list = get_top_fo_stocks()
stock = st.sidebar.selectbox("Select Stock", stock_list)
strategy = st.sidebar.selectbox("Select Strategy", ["Safe", "Min Investment", "Max Profit", "Reversal", "Breakout"])

# Get price and option chain
df_price = get_stock_price_data(stock)
oi_result = get_oi_levels(stock)
df_chain = oi_result["df"]
expiry_list = oi_result["expiries"]
selected_expiry = st.sidebar.selectbox("Select Expiry", expiry_list)

# Filter option chain to selected expiry
df_chain = get_oi_levels(stock, expiry=selected_expiry)["df"]

# Display current price
if not df_price.empty:
    latest_price = df_price["Close"].iloc[-1]
    st.markdown(f"### 📌 Current Price of `{stock}`: ₹{latest_price:.2f}")
else:
    st.warning("Could not fetch price data.")

# -------------------- 🕯️ Candlestick Chart --------------------
st.subheader("🕯️ Candlestick Chart (Last 2 Days)")

if not df_price.empty:
    candles = df_price.reset_index()
    fig_candle = go.Figure(data=[go.Candlestick(
        x=candles['Datetime'],
        open=candles['Open'],
        high=candles['High'],
        low=candles['Low'],
        close=candles['Close']
    )])
    fig_candle.update_layout(height=400, template="plotly_white")
    st.plotly_chart(fig_candle, use_container_width=True)

    # Export CSV
    st.download_button(
        label="⬇️ Download Candlestick Data (CSV)",
        data=df_price.to_csv().encode("utf-8"),
        file_name=f"{stock}_candles.csv",
        mime="text/csv"
    )
else:
    st.warning("No price data available.")

# -------------------- 📊 Option Premium Chart --------------------
st.subheader("📊 Option Premium Chart with Heatmap & Suggestions")

if not df_chain.empty:
    atm_strike = round(latest_price / 50) * 50
    highest_ce = df_chain.loc[df_chain["CE_OI"].idxmax()]
    highest_pe = df_chain.loc[df_chain["PE_OI"].idxmax()]

    suggested_strike = highest_pe["strike"] if strategy in ["Safe", "Reversal"] else highest_ce["strike"]
    suggestion_text = "High PE OI (Support)" if strategy in ["Safe", "Reversal"] else "High CE OI (Resistance)"

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_chain["strike"], y=df_chain["CE_price"],
        mode="markers+lines", name="CE",
        marker=dict(size=(df_chain["CE_OI"] / df_chain["CE_OI"].max()) * 40, color="blue", opacity=0.6)
    ))

    fig.add_trace(go.Scatter(
        x=df_chain["strike"], y=df_chain["PE_price"],
        mode="markers+lines", name="PE",
        marker=dict(size=(df_chain["PE_OI"] / df_chain["PE_OI"].max()) * 40, color="red", opacity=0.6)
    ))

    fig.add_vline(x=atm_strike, line=dict(color="green", dash="dash"), annotation_text="ATM", annotation_position="top right")
    fig.add_vline(x=suggested_strike, line=dict(color="orange", dash="dot"),
                  annotation_text=f"💡 {suggestion_text}", annotation_position="top left")

    fig.update_layout(title=f"{stock} Premiums | Expiry: {selected_expiry}",
                      xaxis_title="Strike", yaxis_title="Premium (₹)",
                      template="plotly_white", legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)

    # Export Chart PNG
    buffer = BytesIO()
    fig.write_image(buffer, format="png")
    st.download_button("⬇️ Download Chart (PNG)", buffer.getvalue(), file_name=f"{stock}_premium_chart.png", mime="image/png")

    # Export Chart HTML
    html_buffer = BytesIO()
    fig.write_html(html_buffer, include_plotlyjs="cdn")
    st.download_button("⬇️ Download Chart (HTML)", html_buffer.getvalue(), file_name=f"{stock}_chart.html", mime="text/html")

    # Telegram Send
    if st.button("📤 Send Suggested Signal to Telegram"):
        signal_text = f"📊 *{stock} Option Signal*\n" \
                      f"💡 Strategy: {strategy}\n" \
                      f"📌 Price: ₹{latest_price:.2f} | ATM: {atm_strike}\n" \
                      f"🎯 Suggested Strike: {suggested_strike} ({suggestion_text})\n" \
                      f"📆 Expiry: {selected_expiry}"
        success = send_telegram_message(signal_text)
        if success:
            st.success("✅ Sent to Telegram!")
        else:
            st.error("❌ Telegram send failed.")

else:
    st.warning("No option chain data available.")

# -------------------- 🧱 OI & Volume Heatmap Table --------------------
st.subheader("📊 OI & Volume Heatmap Table")

if not df_chain.empty:
    heatmap_df = df_chain[["strike", "CE_OI", "PE_OI", "CE_vol", "PE_vol"]].copy()
    heatmap_df = heatmap_df.set_index("strike")
    st.dataframe(heatmap_df.style
        .background_gradient(subset=["CE_OI"], cmap="Blues")
        .background_gradient(subset=["PE_OI"], cmap="Reds")
        .background_gradient(subset=["CE_vol"], cmap="PuBuGn")
        .background_gradient(subset=["PE_vol"], cmap="Oranges"),
        use_container_width=True
    )
