import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from stock_engine import fetch_data, evaluate_signal
from option_chain import get_oi_levels
from telegram_alert import send_telegram_message
from stock_list import get_fo_stocks
from io import BytesIO

# Page setup
st.set_page_config(page_title="📈 Stock Option Analyzer", layout="wide")
st.title("📈 Stock Option Analyzer App")

# Sidebar
st.sidebar.header("🔍 Configuration")
stock_list = get_fo_stocks()
stock = st.sidebar.selectbox("Select Stock", stock_list)
strategy = st.sidebar.selectbox("Select Strategy", ["Safe", "Min Investment", "Max Profit", "Reversal", "Breakout"])
enable_autosend = st.sidebar.checkbox("📤 Enable Auto-Send to Telegram", value=True)

# Load price and option chain data
df_price = fetch_data(stock)
if df_price is None or df_price.empty:
    st.error("Failed to load price data.")
    st.stop()

latest_price = df_price["Close"].iloc[-1]
st.markdown(f"### 📌 Current Price of `{stock}`: ₹{latest_price:.2f}")

oi_result = get_oi_levels(stock)
df_chain = oi_result["df"]

# ----- 🕯️ Candlestick Chart -----
st.subheader("🕯️ Candlestick Chart (Last 2 Days)")
candles = df_price.reset_index()
fig_candle = go.Figure(data=[go.Candlestick(
    x=candles['Datetime'],
    open=candles['Open'], high=candles['High'],
    low=candles['Low'], close=candles['Close']
)])
fig_candle.update_layout(height=400, template="plotly_white")
st.plotly_chart(fig_candle, use_container_width=True)

st.download_button(
    label="⬇️ Download Candlestick Data (CSV)",
    data=df_price.to_csv().encode("utf-8"),
    file_name=f"{stock}_candles.csv",
    mime="text/csv"
)

# ----- 📊 Option Premium Chart -----
st.subheader("📊 Option Premium Chart with Heatmap & Suggestions")

atm_strike = round(latest_price / 50) * 50
highest_ce = df_chain.loc[df_chain["CE_OI"].idxmax()]
highest_pe = df_chain.loc[df_chain["PE_OI"].idxmax()]

suggested_strike = highest_pe["strike"] if strategy in ["Safe", "Reversal"] else highest_ce["strike"]
suggestion_text = "High PE OI (Support)" if strategy in ["Safe", "Reversal"] else "High CE OI (Resistance)"

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_chain["strike"], y=df_chain["CE_price"],
    mode="markers+lines", name="CE",
    marker=dict(size=(df_chain["CE_OI"] / df_chain["CE_OI"].max()) * 40,
                color="blue", opacity=0.6)
))
fig.add_trace(go.Scatter(
    x=df_chain["strike"], y=df_chain["PE_price"],
    mode="markers+lines", name="PE",
    marker=dict(size=(df_chain["PE_OI"] / df_chain["PE_OI"].max()) * 40,
                color="red", opacity=0.6)
))

fig.add_vline(x=atm_strike, line=dict(color="green", dash="dash"),
              annotation_text="ATM", annotation_position="top right")
fig.add_vline(x=suggested_strike, line=dict(color="orange", dash="dot"),
              annotation_text=f"💡 {suggestion_text}", annotation_position="top left")

fig.update_layout(title=f"{stock} Premiums | Strategy: {strategy}",
                  xaxis_title="Strike", yaxis_title="Premium (₹)",
                  template="plotly_white", legend=dict(orientation="h"))
st.plotly_chart(fig, use_container_width=True)

# Export chart
buffer = BytesIO()
fig.write_image(buffer, format="png")
st.download_button("⬇️ Download Chart (PNG)", buffer.getvalue(),
                   file_name=f"{stock}_premium_chart.png", mime="image/png")

html_buffer = BytesIO()
fig.write_html(html_buffer, include_plotlyjs="cdn")
st.download_button("⬇️ Download Chart (HTML)", html_buffer.getvalue(),
                   file_name=f"{stock}_chart.html", mime="text/html")

# ----- 📤 Manual Telegram Send -----
if st.button("📤 Send Suggested Signal to Telegram"):
    signal_text = f"📊 *{stock} Option Signal*\n" \
                  f"💡 Strategy: {strategy}\n" \
                  f"📌 Price: ₹{latest_price:.2f} | ATM: {atm_strike}\n" \
                  f"🎯 Suggested Strike: {suggested_strike} ({suggestion_text})"
    if send_telegram_message(signal_text):
        st.success("✅ Sent to Telegram!")
    else:
        st.error("❌ Telegram send failed.")

# ----- 🧱 OI / Volume Heatmap Table -----
st.subheader("📊 OI & Volume Heatmap Table")

heatmap_df = df_chain[["strike", "CE_OI", "PE_OI", "CE_vol", "PE_vol"]].copy()
heatmap_df = heatmap_df.set_index("strike")
st.dataframe(heatmap_df.style
    .background_gradient(subset=["CE_OI"], cmap="Blues")
    .background_gradient(subset=["PE_OI"], cmap="Reds")
    .background_gradient(subset=["CE_vol"], cmap="PuBuGn")
    .background_gradient(subset=["PE_vol"], cmap="Oranges"),
    use_container_width=True
)

# ----- ⏱️ Auto-Send Logic -----
now = datetime.now()
market_open = now.replace(hour=9, minute=20, second=0, microsecond=0)
market_close = now.replace(hour=15, minute=25, second=0, microsecond=0)

if 'last_sent_time' not in st.session_state:
    st.session_state['last_sent_time'] = now - timedelta(minutes=20)

cooldown = timedelta(minutes=15)
time_since_last = now - st.session_state['last_sent_time']

if enable_autosend and market_open <= now <= market_close:
    if time_since_last > cooldown:
        signal_text = f"📊 *{stock} Option Signal*\n" \
                      f"💡 Strategy: {strategy}\n" \
                      f"📌 Price: ₹{latest_price:.2f} | ATM: {atm_strike}\n" \
                      f"🎯 Suggested Strike: {suggested_strike} ({suggestion_text})"
        if send_telegram_message(signal_text):
            st.success("✅ Auto-signal sent to Telegram")
            st.session_state['last_sent_time'] = now
        else:
            st.warning("❌ Auto-signal failed to send.")
    else:
        mins = int(time_since_last.total_seconds() / 60)
        st.info(f"⏱ Cooldown active. Last signal was sent {mins} min ago.")
