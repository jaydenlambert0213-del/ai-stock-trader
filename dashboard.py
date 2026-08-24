"""Interactive Dashboard - Streamlit web interface for the AI trader."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import yaml

from src.market_data import MarketData
from src.indicators import TechnicalIndicators
from src.ai_engine import AIEngine
from src.portfolio import Portfolio

# Configure page
st.set_page_config(
    page_title="AI Stock Trader Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load configuration
@st.cache_resource
def load_config():
    with open('config/config.yaml', 'r') as f:
        return yaml.safe_load(f)

config = load_config()

# Initialize session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = Portfolio(config.get('trading', {}).get('initial_capital', 100000))

if 'market_data' not in st.session_state:
    st.session_state.market_data = MarketData(config.get('trading', {}).get('symbols', []))

if 'ai_engine' not in st.session_state:
    st.session_state.ai_engine = AIEngine(config)

# Page title
st.title("📈 AI Stock Trader Dashboard")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    page = st.radio(
        "Select Page:",
        ["📊 Overview", "📈 Stock Analysis", "💼 Portfolio", "📋 Trade History", "🧪 Backtest"]
    )
    
    refresh_interval = st.slider("Refresh Interval (seconds)", 30, 300, 60)

# Page: Overview
if page == "📊 Overview":
    st.header("Portfolio Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    pnl = st.session_state.portfolio.get_total_pnl()
    
    with col1:
        st.metric("Total Value", f"${pnl['current_value']:,.2f}")
    
    with col2:
        st.metric("Cash Available", f"${pnl['cash']:,.2f}")
    
    with col3:
        st.metric(
            "Total P&L",
            f"${pnl['total_pnl']:,.2f}",
            f"{pnl['pnl_percent']:.2f}%"
        )
    
    with col4:
        st.metric("Holdings Value", f"${pnl['holdings_value']:,.2f}")
    
    st.markdown("---")
    
    # Holdings
    st.subheader("Current Holdings")
    positions = st.session_state.portfolio.get_all_positions()
    
    if positions:
        positions_df = pd.DataFrame(positions)
        positions_df = positions_df[['symbol', 'shares', 'avg_price', 'current_price', 'current_value', 'pnl', 'pnl_percent']]
        positions_df.columns = ['Symbol', 'Shares', 'Avg Price', 'Current Price', 'Value', 'P&L', 'P&L %']
        
        st.dataframe(
            positions_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No open positions")

# Page: Stock Analysis
elif page == "📈 Stock Analysis":
    st.header("Stock Analysis")
    
    symbols = config.get('trading', {}).get('symbols', [])
    selected_symbol = st.selectbox("Select Stock", symbols)
    
    if selected_symbol:
        # Fetch data
        df = st.session_state.market_data.fetch_data(selected_symbol, period='6mo')
        
        if df is not None:
            # Preprocess and add indicators
            df = st.session_state.market_data.preprocess_data(df)
            df = TechnicalIndicators.calculate_all_indicators(df, config)
            
            # Analyze
            analysis = st.session_state.ai_engine.analyze_stock(df, selected_symbol)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Current Price", f"${analysis['price']:.2f}")
            
            with col2:
                st.metric("Recommendation", analysis['recommendation'])
            
            with col3:
                st.metric("Confidence", f"{analysis['confidence']:.2%}")
            
            st.info(f"📌 {analysis['reason']}")
            
            st.markdown("---")
            
            # Price chart
            fig = go.Figure()
            
            fig.add_trace(go.Candlestick(
                x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Price'
            ))
            
            fig.update_layout(
                title=f"{selected_symbol} Price Chart",
                yaxis_title="Price ($)",
                xaxis_title="Date",
                template="plotly_dark",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Indicators
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Technical Indicators")
                indicators_dict = {
                    'RSI': analysis['signals'].get('RSI', 'N/A'),
                    'MACD': analysis['signals'].get('MACD', 'N/A'),
                    'Bollinger Bands': analysis['signals'].get('BollingerBands', 'N/A'),
                    'Moving Averages': analysis['signals'].get('MovingAverages', 'N/A'),
                }
                
                indicators_df = pd.DataFrame(
                    list(indicators_dict.items()),
                    columns=['Indicator', 'Signal']
                )
                
                st.dataframe(indicators_df, use_container_width=True, hide_index=True)
            
            with col2:
                st.subheader("Signal Scores")
                scores = analysis['scores']
                if scores:
                    fig_scores = px.bar(
                        x=list(scores.keys()),
                        y=list(scores.values()),
                        title="Indicator Confidence Scores",
                        color=list(scores.values()),
                        color_continuous_scale="RdYlGn",
                        range_color=[0, 1]
                    )
                    fig_scores.update_layout(template="plotly_dark", height=400)
                    st.plotly_chart(fig_scores, use_container_width=True)

# Page: Portfolio
elif page == "💼 Portfolio":
    st.header("Portfolio Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Current Holdings")
        positions = st.session_state.portfolio.get_all_positions()
        if positions:
            for pos in positions:
                st.write(f"**{pos['symbol']}**: {pos['shares']:.0f} shares @ ${pos['avg_price']:.2f}")
                st.progress(min(pos['pnl_percent'] / 10 + 0.5, 1.0))
        else:
            st.info("No open positions")
    
    with col2:
        st.subheader("Portfolio Allocation")
        pnl = st.session_state.portfolio.get_total_pnl()
        
        if positions:
            symbols = [p['symbol'] for p in positions]
            values = [p['current_value'] for p in positions]
            
            fig_pie = px.pie(
                values=values,
                names=symbols,
                title="Portfolio Allocation"
            )
            fig_pie.update_layout(template="plotly_dark", height=400)
            st.plotly_chart(fig_pie, use_container_width=True)

# Page: Trade History
elif page == "📋 Trade History":
    st.header("Trade History")
    
    trades_df = st.session_state.portfolio.get_trade_history()
    
    if not trades_df.empty:
        st.dataframe(
            trades_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Trade statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Trades", len(trades_df))
        
        with col2:
            buy_trades = len(trades_df[trades_df['type'] == 'BUY'])
            st.metric("Buy Trades", buy_trades)
        
        with col3:
            sell_trades = len(trades_df[trades_df['type'] == 'SELL'])
            st.metric("Sell Trades", sell_trades)
    else:
        st.info("No trades executed yet")

# Page: Backtest
elif page == "🧪 Backtest":
    st.header("Strategy Backtesting")
    
    st.info("⚠️ Backtesting requires running the backtest.py script separately.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Backtest Parameters")
        backtest_config = config.get('backtesting', {})
        st.write(f"**Initial Capital**: ${backtest_config.get('initial_capital', 100000):,}")
        st.write(f"**Commission**: {backtest_config.get('commission', 0.001)*100:.2f}%")
        st.write(f"**Slippage**: {backtest_config.get('slippage', 0.0005)*100:.3f}%")
    
    with col2:
        st.subheader("Instructions")
        st.markdown("""
        1. Run backtest from terminal:
           ```bash
           python backtest.py
           ```
        2. Results will be displayed here
        3. Analyze performance metrics
        """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center'><small>AI Stock Trader | Last Updated: " + 
    datetime.now().strftime("%Y-%m-%d %H:%M:%S") + 
    "</small></div>",
    unsafe_allow_html=True
)
