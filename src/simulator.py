"""Trade Simulator - Simulates trade execution."""

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TradeSimulator:
    """Simulates trade execution with realistic slippage and fees."""
    
    def __init__(self, commission: float = 0.001, slippage: float = 0.0005):
        """
        Initialize TradeSimulator.
        
        Args:
            commission: Commission rate (0.001 = 0.1%)
            slippage: Slippage rate
        """
        self.commission = commission
        self.slippage = slippage
        self.trades = []
    
    def simulate_buy(self, symbol: str, shares: float, price: float, 
                    timestamp: datetime = None) -> Dict:
        """
        Simulate a buy trade.
        
        Args:
            symbol: Stock symbol
            shares: Number of shares
            price: Bid price
            timestamp: Trade timestamp
            
        Returns:
            Dictionary with execution details
        """
        # Apply slippage
        execution_price = price * (1 + self.slippage)
        
        # Calculate costs
        gross_cost = shares * execution_price
        commission_cost = gross_cost * self.commission
        total_cost = gross_cost + commission_cost
        
        trade = {
            'timestamp': timestamp or datetime.now(),
            'symbol': symbol,
            'type': 'BUY',
            'shares': shares,
            'bid_price': price,
            'execution_price': execution_price,
            'gross_cost': gross_cost,
            'commission': commission_cost,
            'total_cost': total_cost,
            'avg_price': execution_price
        }
        
        self.trades.append(trade)
        logger.info(f"Simulated BUY: {shares} {symbol} @ ${execution_price:.2f}")
        
        return trade
    
    def simulate_sell(self, symbol: str, shares: float, price: float,
                     timestamp: datetime = None) -> Dict:
        """
        Simulate a sell trade.
        
        Args:
            symbol: Stock symbol
            shares: Number of shares
            price: Ask price
            timestamp: Trade timestamp
            
        Returns:
            Dictionary with execution details
        """
        # Apply slippage (negative for sell)
        execution_price = price * (1 - self.slippage)
        
        # Calculate proceeds
        gross_proceeds = shares * execution_price
        commission_cost = gross_proceeds * self.commission
        net_proceeds = gross_proceeds - commission_cost
        
        trade = {
            'timestamp': timestamp or datetime.now(),
            'symbol': symbol,
            'type': 'SELL',
            'shares': shares,
            'ask_price': price,
            'execution_price': execution_price,
            'gross_proceeds': gross_proceeds,
            'commission': commission_cost,
            'net_proceeds': net_proceeds,
            'avg_price': execution_price
        }
        
        self.trades.append(trade)
        logger.info(f"Simulated SELL: {shares} {symbol} @ ${execution_price:.2f}")
        
        return trade
    
    def get_trade_history(self) -> pd.DataFrame:
        """
        Get all simulated trades as DataFrame.
        
        Returns:
            DataFrame of trades
        """
        if not self.trades:
            return pd.DataFrame()
        return pd.DataFrame(self.trades)
    
    def clear_history(self):
        """
        Clear trade history."""
        self.trades.clear()
        logger.info("Trade history cleared")
