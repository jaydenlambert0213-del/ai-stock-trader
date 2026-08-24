# AI Stock Trader

An intelligent, automated stock trading system with AI-driven decision-making, risk management, portfolio tracking, and backtesting capabilities.

## Features

- **AI Stock Analysis**: Analyzes stocks using price/volume data and predefined technical indicators
- **Automated Trading**: AI automatically chooses and executes simulated trades based on market conditions
- **Risk Controls**: 
  - Maximum position size limits
  - Stop-loss rules
  - Daily loss limits
  - Position sizing based on risk tolerance
- **Portfolio Manager**: Tracks cash, holdings, profit/loss, and performance metrics
- **Automatic Trading Loop**: Runs continuously during market hours with real-time market data
- **Interactive Dashboard**: Visualizes trades, portfolio status, and AI reasoning
- **Backtesting Engine**: Tests strategies against historical data before live trading
- **Performance Analytics**: Detailed performance reports and strategy metrics

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│           Market Data Provider (yfinance)            │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
┌───────────────────┐         ┌──────────────────┐
│ Technical         │         │ Data Pipeline    │
│ Indicators        │         │ (Preprocessing)  │
└────────┬──────────┘         └────────┬─────────┘
         │                            │
         └────────────┬───────────────┘
                      ▼
            ┌──────────────────────┐
            │   AI Trading Engine  │
            │ (Decision Making)    │
            └──────────┬───────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌────────┐  ┌─────────────┐ ┌──────────────┐
   │ Buy    │  │ Sell        │ │ Risk Manager │
   │Signal  │  │ Signal      │ │ (Validation) │
   └────┬───┘  └────┬────────┘ └──────┬───────┘
        │           │                 │
        └───────────┼─────────────────┘
                    ▼
        ┌──────────────────────┐
        │ Portfolio Manager    │
        │ (Cash, Holdings,     │
        │  P&L, Performance)   │
        └──────────┬───────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
   ┌─────────────┐      ┌─────────────┐
   │ Backtester  │      │ Dashboard   │
   │ (Validation)│      │ (Reporting) │
   └─────────────┘      └─────────────┘
```

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/jaydenlambert0213-del/ai-stock-trader.git
cd ai-stock-trader

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Edit `config/config.yaml` to set your trading parameters:

```yaml
trading:
  initial_capital: 100000
  max_position_size: 0.05  # 5% of portfolio per position
  stop_loss_percent: 2.0
  daily_loss_limit: 5.0
  symbols: ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'NVDA']

indicators:
  rsi_period: 14
  rsi_oversold: 30
  rsi_overbought: 70
  macd_fast: 12
  macd_slow: 26
  bollinger_period: 20
  
backtesting:
  start_date: '2023-01-01'
  end_date: '2024-01-01'
  initial_capital: 100000
```

### Run Backtesting

```bash
python backtest.py --config config/config.yaml --symbols AAPL GOOGL MSFT
```

### Run Live Trading (Simulated)

```bash
python trader.py --config config/config.yaml
```

### Launch Dashboard

```bash
streamlit run dashboard.py
```

## Project Structure

```
ai-stock-trader/
├── README.md
├── requirements.txt
├── config/
│   └── config.yaml
├── src/
│   ├── __init__.py
│   ├── indicators.py           # Technical indicators
│   ├── ai_engine.py            # AI decision making
│   ├── portfolio.py            # Portfolio management
│   ├── risk_manager.py         # Risk controls
│   ├── market_data.py          # Data fetching
│   └── simulator.py            # Trade simulation
├── backtest.py                 # Backtesting script
├── trader.py                   # Live trading loop
├── dashboard.py                # Streamlit dashboard
└── tests/
    ├── test_indicators.py
    ├── test_ai_engine.py
    ├── test_portfolio.py
    └── test_risk_manager.py
```

## Key Components

### 1. Technical Indicators (`src/indicators.py`)
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Moving Averages (SMA, EMA)
- Volume analysis

### 2. AI Engine (`src/ai_engine.py`)
- Signal generation based on multiple indicators
- Confidence scoring
- Trend analysis
- Pattern recognition

### 3. Portfolio Manager (`src/portfolio.py`)
- Cash tracking
- Position management
- P&L calculation
- Performance metrics

### 4. Risk Manager (`src/risk_manager.py`)
- Position sizing
- Stop-loss enforcement
- Daily loss limits
- Risk/reward ratio validation

### 5. Backtester (`backtest.py`)
- Historical data simulation
- Performance analysis
- Sharpe ratio, Sortino ratio calculation
- Drawdown analysis

## Trading Strategy

The AI uses a multi-indicator approach:

1. **Entry Signals**: Combined RSI, MACD, and Bollinger Band signals
2. **Confidence Scoring**: Weighs signal strength across indicators
3. **Position Sizing**: Allocates capital based on risk tolerance
4. **Stop-Loss**: Automatic exit at predefined loss levels
5. **Profit Taking**: Exits winning positions at targets

## Risk Management

- **Position Sizing**: Max 5% of portfolio per position
- **Stop-Loss**: 2% trailing stop-loss on all positions
- **Daily Loss Limit**: Trading stops if daily loss exceeds 5%
- **Diversification**: Spreads capital across multiple stocks
- **Correlation Analysis**: Avoids highly correlated positions

## Performance Metrics

- Total Return
- Annualized Return
- Sharpe Ratio
- Sortino Ratio
- Maximum Drawdown
- Win Rate
- Profit Factor
- Recovery Factor

## Data Source

- **Primary**: Yahoo Finance (yfinance)
- **Frequency**: Daily and intraday data
- **Coverage**: US stocks and major indices

## Disclaimer

This is a simulated trading system for educational purposes. 

⚠️ **NOT for real money trading without significant modifications and proper risk assessment.**

Always backtest strategies thoroughly before considering any live trading. Past performance does not guarantee future results.

## License

MIT License

## Contributing

Contributions are welcome! Please open issues and submit pull requests.

## Support

For questions and issues, please use the GitHub Issues section.
