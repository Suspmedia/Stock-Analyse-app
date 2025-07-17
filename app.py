import streamlit as st
from datetime import date
from stock_list import get_fo_stocks
from stock_engine import fetch_data, generate_stock_signals, backtest_strategy
from option_chain import get_oi_levels
from telegram_alert import send_telegram_message, log_trade, load_trade_log
import plotly.graph_objects as go

st.set_page_config(page_title="📊 Stock Options Analyzer", layout="wide")
st.title("📈 Stock Options Analyzer with Live Signals, Journal & Backtest")

tab1, tab2, tab3 = st.tabs(["📉 Live Signal", "📋 Trade Journal", "🧪 Backtest"])

# ------------------- Tab 1: Live Signal -------------------
with tab1:
    fo_stocks = get_fo_stocks()
    stock = st.sidebar.selectbox("Select F&O Stock", fo_stocks)
    strategy = st.sidebar.radio("Strategy", ["Safe", "Min Investment", "Max Profit", "Reversal", "Breakout"])
    strike_type = st.sidebar.radio("Strike Type", ["ATM", "ITM", "OTM"])
    expiry = st.sidebar.date_input("Select Expiry", value=date.today())
    strike_range = st.sidebar.selectbox("Show Strikes", ["All", "ATM ±1", "ATM ±2", "ATM Only"])

    df_price = fetch_data(stock)
    if df_price is not None:
        current_price = round(df_price["Close"].iloc[-1], 2)
        rsi = round(df_price["RSI"].iloc[-1], 2)
        high_52w = round(df_price["Close"].max(), 2)
        low_52w = round(df_price["Close"].min(), 2)
        st.markdown(f"**Price:** ₹{current_price} | **RSI:** {rsi} | 52W Range: ₹{low_52w} - ₹{high_52w}")

    result = get_oi_levels(stock)
    df_chain = result["df"]

    if not df_chain.empty:
        atm_strike = round(current_price / 50) * 50
        if strike_range == "ATM ±1":
            df_chain = df_chain[(df_chain["strike"] >= atm_strike - 50) & (df_chain["strike"] <= atm_strike + 50)]
        elif strike_range == "ATM ±2":
            df_chain = df_chain[(df_chain["strike"] >= atm_strike - 100) & (df_chain["strike"] <= atm_strike + 100)]
        elif strike_range == "ATM Only":
            df_chain = df_chain[df_chain["strike"] == atm_strike]

        st.subheader("📊 Option Chain")
        st.dataframe(df_chain)

        # --- Premium Chart ---
        st.subheader("📊 Option Premium + OI + Volume Chart")
        signals = generate_stock_signals(stock, strategy, strike_type, expiry)
        suggested_strike = None
        if not signals.empty:
            try:
                suggested_strike = int(signals["Signal"].iloc[0].split()[2])
            except: pass

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_chain["strike"], y=df_chain["CE_price"], name="CE Premium", line=dict(color="blue")))
        fig.add_trace(go.Scatter(x=df_chain["strike"], y=df_chain["PE_price"], name="PE Premium", line=dict(color="red")))
        fig.add_trace(go.Scatter(x=df_chain["strike"], y=df_chain["CE_OI"]/1000, name="CE OI", line=dict(color="blue", dash="dot")))
        fig.add_trace(go.Scatter(x=df_chain["strike"], y=df_chain["PE_OI"]/1000, name="PE OI", line=dict(color="red", dash="dot")))
        fig.add_trace(go.Bar(x=df_chain["strike"], y=df_chain["CE_vol"], name="CE Volume", opacity=0.4, yaxis='y2'))
        fig.add_trace(go.Bar(x=df_chain["strike"], y=df_chain["PE_vol"], name="PE Volume", opacity=0.4, yaxis='y2'))

        if suggested_strike:
            fig.add_vline(x=suggested_strike, line_width=2, line_dash="dash", line_color="green",
                          annotation_text="Suggested", annotation_position="top right")

        fig.update_layout(
            xaxis_title="Strike",
            yaxis=dict(title="Premium / OI"),
            yaxis2=dict(title="Volume", overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", y=-0.2),
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Export
        st.download_button("📥 Download Option Chain", data=df_chain.to_csv(index=False).encode(), file_name=f"{stock}_option_chain.csv")

    # --- Signal Display & Telegram ---
    st.subheader("🔔 Trade Signal")
    if not signals.empty:
        st.dataframe(signals)
        row = signals.iloc[0]
        msg = f"🔔 *Signal:* {row['Signal']}\n💰 Entry: {row['Entry']} | 🎯 Target: {row['Target']} | 🛑 SL: {row['Stop Loss']}\n📌 Strategy: {row['Strategy']} | 📆 Expiry: {row['Expiry']}"
        if st.button("📤 Send to Telegram"):
            sent = send_telegram_message(msg)
            if sent:
                log_trade(row)
                st.success("✅ Sent to Telegram & Logged")
            else:
                st.error("❌ Failed to send to Telegram")
    else:
        st.warning("⚠️ No signal generated for selected strategy")

# ------------------- Tab 2: Trade Journal -------------------
with tab2:
    st.subheader("📋 Trade Journal")
    df_log = load_trade_log()
    if not df_log.empty:
        st.dataframe(df_log)
        st.download_button("Download Trade Log", df_log.to_csv(index=False).encode(), "trade_log.csv")
    else:
        st.info("No trades logged yet.")

# ------------------- Tab 3: Backtest -------------------
with tab3:
    st.subheader("🧪 Strategy Backtest (5-day)")
    selected_strategy = st.selectbox("Select Strategy", ["Safe", "Min Investment", "Max Profit", "Reversal", "Breakout"])
    result_df = backtest_strategy(stock, selected_strategy)
    if not result_df.empty:
        st.dataframe(result_df)
        win_rate = round((result_df["Result"] == "Win").sum() / len(result_df) * 100, 2)
        st.success(f"✅ Win Rate: {win_rate}%")
    else:
        st.warning("No backtest data found.")
