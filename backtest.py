"""Backtesting engine - Tests trading strategies against historical data."""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
import logging

from src.market_data import MarketData
from src.indicators import TechnicalIndicators
from src.ai_engine import AIEngine
from src.portfolio import Portfolio
from src.risk_manager import RiskManager
from src.simulator import TradeSimulator

logger = logging.getLogger(__name__)


class Backtester:
    """Backtests trading strategies using historical data."""
    
    def __init__(self, config: Dict):
        """
        Initialize Backtester.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.backtest_config = config.get('backtesting', {})
        self.market_data = MarketData(config.get('trading', {}).get('symbols', []))
        self.ai_engine = AIEngine(config)
        self.risk_manager = RiskManager(config)
        self.simulator = TradeSimulator(
            commission=self.backtest_config.get('commission', 0.001),
            slippage=self.backtest_config.get('slippage', 0.0005)
        )
        self.portfolio = None
        self.results = None
    
    def run_backtest(self, symbols: List[str], start_date: str = None, 
                    end_date: str = None) -> Dict:
        """
        Run backtest on historical data.
        
        Args:
            symbols: List of symbols to backtest
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Backtest results dictionary
        """
        # Initialize portfolio
        initial_capital = self.backtest_config.get('initial_capital', 100000)
        self.portfolio = Portfolio(initial_capital)
        
        # Use config dates if not provided
        if not start_date:
            start_date = self.backtest_config.get('start_date', '2023-01-01')
        if not end_date:
            end_date = self.backtest_config.get('end_date', '2024-01-01')
        
        # Fetch historical data
        all_data = {}
        for symbol in symbols:
            df = self.market_data.fetch_data(symbol, period='5y')
            if df is not None:
                # Filter by date range
                df['Date'] = pd.to_datetime(df['Date'])
                df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)].reset_index(drop=True)
                
                # Preprocess and add indicators
                df = self.market_data.preprocess_data(df)
                df = TechnicalIndicators.calculate_all_indicators(df, self.config)
                all_data[symbol] = df
        
        if not all_data:
            logger.error("No data retrieved for backtest")
            return {}
        
        # Run backtest
        logger.info(f"Starting backtest from {start_date} to {end_date}")
        
        # Get date range from data
        all_dates = set()
        for df in all_data.values():
            all_dates.update(df['Date'].unique())
        all_dates = sorted(list(all_dates))
        
        # Daily loop
        for date in all_dates:
            # Get data for this date
            daily_data = {}
            for symbol, df in all_data.items():
                day_df = df[df['Date'] == date]
                if not day_df.empty:
                    daily_data[symbol] = day_df
            
            # Analyze and trade
            for symbol, day_df in daily_data.items():
                self._process_daily_symbol(symbol, day_df)
        
        # Calculate results
        self.results = self._calculate_results(all_data)
        
        return self.results
    
    def _process_daily_symbol(self, symbol: str, day_df: pd.DataFrame):
        """
        Process daily data for a symbol and execute trades.
        
        Args:
            symbol: Stock symbol
            day_df: DataFrame with data for the day
        """
        if day_df.empty:
            return
        
        latest_data = day_df.iloc[-1]
        current_price = latest_data['Close']
        
        # Update prices
        self.portfolio.update_price(symbol, current_price)
        
        # Check stop losses and take profits
        if symbol in self.portfolio.holdings:
            holding = self.portfolio.holdings[symbol]
            entry_price = holding['avg_price']
            
            # Check stop loss
            if self.risk_manager.check_stop_loss_hit(current_price, entry_price):
                self.portfolio.sell(symbol, holding['shares'], current_price)
                logger.info(f"Stop loss hit for {symbol}")
                return
            
            # Check take profit
            if self.risk_manager.check_take_profit_hit(current_price, entry_price):
                self.portfolio.sell(symbol, holding['shares'], current_price)
                logger.info(f"Take profit hit for {symbol}")
                return
        
        # Generate trading signal
        analysis = self.ai_engine.analyze_stock(day_df, symbol)
        
        if analysis['recommendation'] == 'BUY' and analysis['confidence'] > self.ai_engine.min_confidence:
            # Check if we already have a position
            if symbol not in self.portfolio.holdings:
                # Validate trade
                portfolio_value = self.portfolio.get_total_value()
                valid, reason = self.risk_manager.validate_buy_trade(
                    symbol, 1, current_price, portfolio_value, 
                    self.portfolio.cash, len(self.portfolio.holdings)
                )
                
                if valid:
                    # Calculate position size
                    shares = self.risk_manager.calculate_position_size(
                        portfolio_value, symbol, current_price,
                        self.risk_manager.calculate_stop_loss(current_price)
                    )
                    
                    if self.portfolio.buy(symbol, shares, current_price):
                        logger.info(f"BUY signal for {symbol}: {analysis['reason']}")
        
        elif analysis['recommendation'] == 'SELL' and symbol in self.portfolio.holdings:
            holding = self.portfolio.holdings[symbol]
            if self.portfolio.sell(symbol, holding['shares'], current_price):
                logger.info(f"SELL signal for {symbol}: {analysis['reason']}")
    
    def _calculate_results(self, all_data: Dict) -> Dict:
        """
        Calculate backtest results and metrics.
        
        Args:
            all_data: Dictionary of all historical data
            
        Returns:
            Results dictionary with metrics
        """
        pnl = self.portfolio.get_total_pnl()
        trades_df = self.portfolio.get_trade_history()
        
        # Calculate metrics
        total_trades = len(trades_df)
        buy_trades = len(trades_df[trades_df['type'] == 'BUY'])
        sell_trades = len(trades_df[trades_df['type'] == 'SELL'])
        
        # Win rate
        winning_trades = 0
        losing_trades = 0
        
        if not trades_df.empty:
            for i in range(0, len(trades_df), 2):
                if i + 1 < len(trades_df):
                    buy_price = trades_df.iloc[i]['price']
                    sell_price = trades_df.iloc[i+1]['price']
                    if sell_price > buy_price:
                        winning_trades += 1
                    else:
                        losing_trades += 1
        
        win_rate = (winning_trades / (winning_trades + losing_trades) * 100) if (winning_trades + losing_trades) > 0 else 0
        
        # Calculate returns
        total_return = pnl['total_pnl']
        total_return_pct = pnl['pnl_percent']
        
        # Estimate Sharpe ratio (simplified)
        sharpe_ratio = self._calculate_sharpe_ratio(all_data)
        
        results = {
            'initial_capital': self.portfolio.initial_capital,
            'final_value': pnl['current_value'],
            'total_return': total_return,
            'total_return_percent': total_return_pct,
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate_percent': win_rate,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': self._calculate_max_drawdown(),
            'portfolio_history': self.portfolio.performance_history,
            'trades': trades_df.to_dict('records') if not trades_df.empty else []
        }
        
        return results
    
    def _calculate_sharpe_ratio(self, all_data: Dict) -> float:
        """
        Calculate Sharpe ratio (simplified).
        
        Args:
            all_data: Dictionary of all historical data
            
        Returns:
            Sharpe ratio
        """
        try:
            # Calculate returns from benchmark (first symbol)
            if all_data:
                first_symbol = list(all_data.keys())[0]
                df = all_data[first_symbol]
                returns = df['Close'].pct_change().dropna()
                
                if len(returns) > 0:
                    avg_return = returns.mean() * 252  # Annualized
                    std_return = returns.std() * np.sqrt(252)  # Annualized
                    
                    risk_free_rate = 0.02
                    if std_return > 0:
                        return (avg_return - risk_free_rate) / std_return
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {e}")
        
        return 0.0
    
    def _calculate_max_drawdown(self) -> float:
        """
        Calculate maximum drawdown.
        
        Returns:
            Maximum drawdown percentage
        """
        try:
            portfolio_values = [self.portfolio.initial_capital]
            
            for trade in self.portfolio.trades:
                if trade['type'] == 'BUY':
                    portfolio_values.append(portfolio_values[-1] - trade['total'])
                else:
                    portfolio_values.append(portfolio_values[-1] + trade['total'])
            
            peak = 0
            max_drawdown = 0
            
            for value in portfolio_values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak if peak > 0 else 0
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            return max_drawdown * 100
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return 0.0
    
    def print_results(self):
        """
        Print backtest results in readable format."""
        if not self.results:
            print("No backtest results available")
            return
        
        print("\n" + "="*80)
        print("BACKTEST RESULTS")
        print("="*80)
        print(f"Initial Capital:        ${self.results['initial_capital']:,.2f}")
        print(f"Final Portfolio Value:  ${self.results['final_value']:,.2f}")
        print(f"Total Return:           ${self.results['total_return']:,.2f}")
        print(f"Return Percentage:      {self.results['total_return_percent']:.2f}%")
        print(f"\nTrade Statistics:")
        print(f"  Total Trades:         {self.results['total_trades']}")
        print(f"  Buy Trades:           {self.results['buy_trades']}")
        print(f"  Sell Trades:          {self.results['sell_trades']}")
        print(f"  Winning Trades:       {self.results['winning_trades']}")
        print(f"  Losing Trades:        {self.results['losing_trades']}")
        print(f"  Win Rate:             {self.results['win_rate_percent']:.2f}%")
        print(f"\nRisk Metrics:")
        print(f"  Sharpe Ratio:         {self.results['sharpe_ratio']:.4f}")
        print(f"  Max Drawdown:         {self.results['max_drawdown']:.2f}%")
        print("="*80 + "\n")
