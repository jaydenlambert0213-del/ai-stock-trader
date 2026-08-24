"""Live trading loop - Runs the AI trader during market hours."""

import time
import yaml
import logging
from datetime import datetime, time as datetime_time
from typing import Dict, List

from src.market_data import MarketData
from src.indicators import TechnicalIndicators
from src.ai_engine import AIEngine
from src.portfolio import Portfolio
from src.risk_manager import RiskManager
from src.simulator import TradeSimulator

logger = logging.getLogger(__name__)


class LiveTrader:
    """Manages live trading operations."""
    
    def __init__(self, config_path: str):
        """
        Initialize LiveTrader.
        
        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.symbols = self.config.get('trading', {}).get('symbols', [])
        self.market_data = MarketData(self.symbols)
        self.ai_engine = AIEngine(self.config)
        self.risk_manager = RiskManager(self.config)
        self.simulator = TradeSimulator()
        self.portfolio = Portfolio(self.config.get('trading', {}).get('initial_capital', 100000))
        
        self.trading_hours = self.config.get('trading_hours', {})
        self.is_trading = False
        self.trade_count = 0
    
    def is_market_open(self) -> bool:
        """
        Check if market is currently open.
        
        Returns:
            True if market is open
        """
        now = datetime.now()
        current_time = now.time()
        
        start_hour = self.trading_hours.get('start_hour', 9)
        start_minute = self.trading_hours.get('start_minute', 30)
        end_hour = self.trading_hours.get('end_hour', 16)
        end_minute = self.trading_hours.get('end_minute', 0)
        
        start_time = datetime_time(start_hour, start_minute)
        end_time = datetime_time(end_hour, end_minute)
        
        # Check if weekday and during trading hours
        is_weekday = now.weekday() < 5  # Monday=0, Friday=4
        is_trading_hours = start_time <= current_time <= end_time
        
        return is_weekday and is_trading_hours
    
    def update_prices(self):
        """
        Fetch and update current prices for all symbols."""
        logger.info("Updating prices...")
        current_data = self.market_data.get_current_data(self.symbols)
        
        for _, row in current_data.iterrows():
            symbol = row['Symbol']
            price = row['Price']
            self.portfolio.update_price(symbol, price)
    
    def analyze_and_trade(self):
        """
        Analyze all symbols and execute trades."""
        if not self.is_market_open():
            logger.info("Market is closed")
            return
        
        logger.info(f"Starting analysis at {datetime.now()}")
        
        for symbol in self.symbols:
            try:
                # Fetch latest data
                df = self.market_data.fetch_data(symbol, period='3mo')
                
                if df is None or df.empty:
                    logger.warning(f"No data for {symbol}")
                    continue
                
                # Preprocess and add indicators
                df = self.market_data.preprocess_data(df)
                df = TechnicalIndicators.calculate_all_indicators(df, self.config)
                
                # Analyze stock
                analysis = self.ai_engine.analyze_stock(df, symbol)
                
                current_price = analysis['price']
                
                # Update portfolio price
                self.portfolio.update_price(symbol, current_price)
                
                # Check stop losses and take profits
                self._check_exits(symbol, current_price, df)
                
                # Process buy/sell signals
                self._process_signal(symbol, analysis, current_price)
                
                # Print analysis
                logger.info(self.ai_engine.get_signal_explanation(analysis))
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {str(e)}")
    
    def _check_exits(self, symbol: str, current_price: float, df: pd.DataFrame):
        """
        Check and execute stop losses and take profits.
        
        Args:
            symbol: Stock symbol
            current_price: Current price
            df: Price data
        """
        if symbol not in self.portfolio.holdings:
            return
        
        holding = self.portfolio.holdings[symbol]
        entry_price = holding['avg_price']
        
        # Check stop loss
        if self.risk_manager.check_stop_loss_hit(current_price, entry_price):
            self.portfolio.sell(symbol, holding['shares'], current_price)
            logger.info(f"STOP LOSS executed for {symbol} at ${current_price:.2f}")
            return
        
        # Check take profit
        if self.risk_manager.check_take_profit_hit(current_price, entry_price):
            self.portfolio.sell(symbol, holding['shares'], current_price)
            logger.info(f"TAKE PROFIT executed for {symbol} at ${current_price:.2f}")
            return
    
    def _process_signal(self, symbol: str, analysis: Dict, current_price: float):
        """
        Process buy/sell signals.
        
        Args:
            symbol: Stock symbol
            analysis: Analysis results
            current_price: Current price
        """
        recommendation = analysis['recommendation']
        confidence = analysis['confidence']
        
        if recommendation == 'BUY' and confidence > self.ai_engine.min_confidence:
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
                        self.trade_count += 1
                        logger.info(f"BUY {symbol}: {analysis['reason']}")
                else:
                    logger.warning(f"Trade validation failed for {symbol}: {reason}")
        
        elif recommendation == 'SELL' and symbol in self.portfolio.holdings:
            holding = self.portfolio.holdings[symbol]
            if self.portfolio.sell(symbol, holding['shares'], current_price):
                self.trade_count += 1
                logger.info(f"SELL {symbol}: {analysis['reason']}")
    
    def print_portfolio_status(self):
        """
        Print current portfolio status."""
        pnl = self.portfolio.get_total_pnl()
        positions = self.portfolio.get_all_positions()
        
        print("\n" + "="*80)
        print("PORTFOLIO STATUS")
        print("="*80)
        print(f"Cash: ${pnl['cash']:,.2f}")
        print(f"Holdings Value: ${pnl['holdings_value']:,.2f}")
        print(f"Total Value: ${pnl['current_value']:,.2f}")
        print(f"Total P&L: ${pnl['total_pnl']:,.2f} ({pnl['pnl_percent']:.2f}%)")
        print(f"\nOpen Positions: {len(positions)}")
        for pos in positions:
            print(f"  {pos['symbol']}: {pos['shares']:.0f} @ ${pos['avg_price']:.2f} = ${pos['current_value']:.2f} (P&L: ${pos['pnl']:.2f})")
        print("="*80 + "\n")
    
    def run(self, check_interval: int = 300):
        """
        Run the trading loop.
        
        Args:
            check_interval: Interval between checks in seconds (default 5 min)
        """
        logger.info("Starting AI Stock Trader...")
        self.is_trading = True
        
        try:
            while self.is_trading:
                if self.is_market_open():
                    self.update_prices()
                    self.analyze_and_trade()
                    self.print_portfolio_status()
                    
                    logger.info(f"Next check in {check_interval} seconds...")
                    time.sleep(check_interval)
                else:
                    logger.info("Waiting for market to open...")
                    time.sleep(60)  # Check every minute if market is open
        
        except KeyboardInterrupt:
            logger.info("Trading stopped by user")
            self.stop()
    
    def stop(self):
        """
        Stop the trading loop."""
        self.is_trading = False
        self.print_portfolio_status()
        logger.info(f"Trading stopped. Total trades executed: {self.trade_count}")


if __name__ == "__main__":
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/trading.log'),
            logging.StreamHandler()
        ]
    )
    
    config_path = sys.argv[1] if len(sys.argv) > 1 else 'config/config.yaml'
    
    trader = LiveTrader(config_path)
    trader.run()
