import streamlit as st
from datetime import date
from stock_list import get_fo_stocks
from stock_engine import fetch_data, generate_stock_signals, backtest_strategy
from option_chain import get_oi_levels
from telegram_alert import send_telegram_message, log_trade, load_trade_log
import plotly.graph_objects as go
import time

# Configure page
st.set_page_config(
    page_title="📊 Stock Options Analyzer",
    layout="wide",
    page_icon="📈"
)
st.title("📈 Stock Options Analyzer with Live Signals, Journal & Backtest")

# Initialize session state for caching
if 'fo_stocks' not in st.session_state:
    st.session_state.fo_stocks = []

# ------------------- Helper Functions -------------------
def safe_get_fo_stocks():
    """Wrapper with error handling for stock list fetching"""
    with st.spinner("Fetching F&O stocks..."):
        try:
            if not st.session_state.fo_stocks:
                st.session_state.fo_stocks = get_fo_stocks()
            return st.session_state.fo_stocks
        except Exception as e:
            st.error(f"Error loading stocks: {str(e)}")
            return []

def display_price_info(df_price):
    """Display price information with proper error handling"""
    if df_price is None or df_price.empty:
        st.error("Failed to fetch price data")
        return None
    
    current_price = round(df_price["Close"].iloc[-1], 2)
    rsi = round(df_price["RSI"].iloc[-1], 2)
    high_52w = round(df_price["Close"].max(), 2)
    low_52w = round(df_price["Close"].min(), 2)
    
    st.markdown(f"""
        **Price:** ₹{current_price} | 
        **RSI:** {rsi} | 
        52W Range: ₹{low_52w} - ₹{high_52w}
    """)
    return current_price

# ------------------- Main Tabs -------------------
tab1, tab2, tab3 = st.tabs(["📉 Live Signal", "📋 Trade Journal", "🧪 Backtest"])

# ------------------- Tab 1: Live Signal -------------------
with tab1:
    # Stock selection with error handling
    fo_stocks = safe_get_fo_stocks()
    if not fo_stocks:
        st.warning("Using limited stock list. Some features may be restricted.")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        stock = st.selectbox("Select F&O Stock", fo_stocks)
        strategy = st.radio("Strategy", ["Safe", "Min Investment", "Max Profit", "Reversal", "Breakout"])
        strike_type = st.radio("Strike Type", ["ATM", "ITM", "OTM"])
    
    with col2:
        expiry = st.date_input("Select Expiry", value=date.today())
        strike_range = st.selectbox("Show Strikes", ["All", "ATM ±1", "ATM ±2", "ATM Only"])

    # Fetch and display price data
    with st.spinner("Fetching market data..."):
        df_price = fetch_data(stock)
        current_price = display_price_info(df_price)
    
    if current_price is None:
        st.stop()  # Stop execution if no price data

    # Fetch option chain
    with st.spinner("Loading option chain..."):
        try:
            result = get_oi_levels(stock)
            df_chain = result.get("df", pd.DataFrame())
            
            if df_chain.empty:
                raise ValueError("Empty option chain")
        except Exception as e:
            st.error(f"Failed to fetch option chain: {str(e)}")
            st.stop()

    # Process option chain
    atm_strike = round(current_price / 50) * 50
    if strike_range == "ATM ±1":
        df_chain = df_chain[(df_chain["strike"] >= atm_strike - 50) & (df_chain["strike"] <= atm_strike + 50)]
    elif strike_range == "ATM ±2":
        df_chain = df_chain[(df_chain["strike"] >= atm_strike - 100) & (df_chain["strike"] <= atm_strike + 100)]
    elif strike_range == "ATM Only":
        df_chain = df_chain[df_chain["strike"] == atm_strike]

    # Display option chain
    st.subheader("📊 Option Chain")
    st.dataframe(
        df_chain.style.format({
            "CE_price": "{:.2f}",
            "PE_price": "{:.2f}",
            "CE_OI": "{:,}",
            "PE_OI": "{:,}",
            "CE_vol": "{:,}",
            "PE_vol": "{:,}"
        }),
        height=400
    )

    # Generate signals
    with st.spinner("Generating signals..."):
        signals = generate_stock_signals(stock, strategy, strike_type, expiry)
    
    # Premium Chart
    st.subheader("📊 Option Premium + OI + Volume Chart")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_chain["strike"], y=df_chain["CE_price"], name="CE Premium", line=dict(color="blue")))
    fig.add_trace(go.Scatter(x=df_chain["strike"], y=df_chain["PE_price"], name="PE Premium", line=dict(color="red")))
    fig.add_trace(go.Scatter(x=df_chain["strike"], y=df_chain["CE_OI"]/1000, name="CE OI", line=dict(color="blue", dash="dot")))
    fig.add_trace(go.Scatter(x=df_chain["strike"], y=df_chain["PE_OI"]/1000, name="PE OI", line=dict(color="red", dash="dot")))
    fig.add_trace(go.Bar(x=df_chain["strike"], y=df_chain["CE_vol"], name="CE Volume", opacity=0.4, yaxis='y2'))
    fig.add_trace(go.Bar(x=df_chain["strike"], y=df_chain["PE_vol"], name="PE Volume", opacity=0.4, yaxis='y2'))

    if not signals.empty:
        try:
            suggested_strike = int(signals["Signal"].iloc[0].split()[2])
            fig.add_vline(
                x=suggested_strike,
                line_width=2,
                line_dash="dash",
                line_color="green",
                annotation_text="Suggested",
                annotation_position="top right"
            )
        except:
            pass

    fig.update_layout(
        xaxis_title="Strike",
        yaxis=dict(title="Premium / OI"),
        yaxis2=dict(title="Volume", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=-0.2),
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Signal Display & Telegram
    st.subheader("🔔 Trade Signal")
    if not signals.empty:
        st.dataframe(signals)
        row = signals.iloc[0]
        msg = f"""🔔 *Signal:* {row['Signal']}
💰 Entry: {row['Entry']} | 🎯 Target: {row['Target']} | 🛑 SL: {row['Stop Loss']}
📌 Strategy: {row['Strategy']} | 📆 Expiry: {row['Expiry']}"""
        
        if st.button("📤 Send to Telegram"):
            if send_telegram_message(msg):
                log_trade(row)
                st.success("✅ Sent to Telegram & Logged")
            else:
                st.error("❌ Failed to send to Telegram")
    else:
        st.warning("⚠️ No signal generated for selected strategy")

    # Export
    st.download_button(
        "📥 Download Option Chain",
        data=df_chain.to_csv(index=False).encode(),
        file_name=f"{stock}_option_chain.csv",
        mime="text/csv"
    )

# ------------------- Tab 2: Trade Journal -------------------
with tab2:
    st.subheader("📋 Trade Journal")
    try:
        df_log = load_trade_log()
        if not df_log.empty:
            st.dataframe(df_log)
            st.download_button(
                "Download Trade Log",
                df_log.to_csv(index=False).encode(),
                "trade_log.csv",
                mime="text/csv"
            )
        else:
            st.info("No trades logged yet.")
    except Exception as e:
        st.error(f"Error loading trade journal: {str(e)}")

# ------------------- Tab 3: Backtest -------------------
with tab3:
    st.subheader("🧪 Strategy Backtest (5-day)")
    selected_strategy = st.selectbox(
        "Select Strategy",
        ["Safe", "Min Investment", "Max Profit", "Reversal", "Breakout"],
        key="backtest_strategy"
    )
    
    with st.spinner("Running backtest..."):
        result_df = backtest_strategy(stock, selected_strategy)
    
    if not result_df.empty:
        st.dataframe(result_df)
        win_rate = round((result_df["Result"] == "Win").sum() / len(result_df) * 100, 2)
        st.success(f"✅ Win Rate: {win_rate}%")
    else:
        st.warning("No backtest data found for selected strategy")
