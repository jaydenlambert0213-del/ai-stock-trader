"""Portfolio management module."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Portfolio:
    """Manages portfolio holdings, cash, and performance metrics."""
    
    def __init__(self, initial_capital: float):
        """
        Initialize portfolio.
        
        Args:
            initial_capital: Initial cash amount
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.holdings = {}  # {symbol: {shares, avg_price, current_price}}
        self.trades = []  # List of all trades executed
        self.performance_history = []  # Daily performance tracking
        
    def buy(self, symbol: str, shares: float, price: float, timestamp: datetime = None) -> bool:
        """
        Record a buy order.
        
        Args:
            symbol: Stock symbol
            shares: Number of shares
            price: Price per share
            timestamp: Trade timestamp
            
        Returns:
            True if successful, False otherwise
        """
        cost = shares * price
        
        if self.cash < cost:
            logger.warning(f"Insufficient cash. Need {cost}, have {self.cash}")
            return False
        
        self.cash -= cost
        
        if symbol not in self.holdings:
            self.holdings[symbol] = {
                'shares': shares,
                'avg_price': price,
                'current_price': price,
                'buy_price': price,
                'entry_time': timestamp or datetime.now()
            }
        else:
            # Calculate new average price
            old_value = self.holdings[symbol]['shares'] * self.holdings[symbol]['avg_price']
            new_value = shares * price
            self.holdings[symbol]['shares'] += shares
            self.holdings[symbol]['avg_price'] = (old_value + new_value) / self.holdings[symbol]['shares']
            self.holdings[symbol]['current_price'] = price
        
        self.trades.append({
            'timestamp': timestamp or datetime.now(),
            'symbol': symbol,
            'type': 'BUY',
            'shares': shares,
            'price': price,
            'total': cost
        })
        
        logger.info(f"BUY: {shares} {symbol} @ ${price:.2f} = ${cost:.2f}")
        return True
    
    def sell(self, symbol: str, shares: float, price: float, timestamp: datetime = None) -> bool:
        """
        Record a sell order.
        
        Args:
            symbol: Stock symbol
            shares: Number of shares
            price: Price per share
            timestamp: Trade timestamp
            
        Returns:
            True if successful, False otherwise
        """
        if symbol not in self.holdings or self.holdings[symbol]['shares'] < shares:
            logger.warning(f"Cannot sell {shares} {symbol}. Holdings: {self.holdings.get(symbol, {}).get('shares', 0)}")
            return False
        
        revenue = shares * price
        self.cash += revenue
        self.holdings[symbol]['shares'] -= shares
        self.holdings[symbol]['current_price'] = price
        
        # Remove position if fully closed
        if self.holdings[symbol]['shares'] == 0:
            del self.holdings[symbol]
        
        self.trades.append({
            'timestamp': timestamp or datetime.now(),
            'symbol': symbol,
            'type': 'SELL',
            'shares': shares,
            'price': price,
            'total': revenue
        })
        
        logger.info(f"SELL: {shares} {symbol} @ ${price:.2f} = ${revenue:.2f}")
        return True
    
    def update_price(self, symbol: str, price: float):
        """
        Update current price for a holding.
        
        Args:
            symbol: Stock symbol
            price: Current price
        """
        if symbol in self.holdings:
            self.holdings[symbol]['current_price'] = price
    
    def get_position_value(self, symbol: str) -> float:
        """
        Get current market value of a position.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Market value of position
        """
        if symbol not in self.holdings:
            return 0.0
        
        holding = self.holdings[symbol]
        return holding['shares'] * holding['current_price']
    
    def get_position_pnl(self, symbol: str) -> Dict:
        """
        Get P&L for a position.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with P&L metrics
        """
        if symbol not in self.holdings:
            return {}
        
        holding = self.holdings[symbol]
        current_value = holding['shares'] * holding['current_price']
        cost_basis = holding['shares'] * holding['avg_price']
        pnl = current_value - cost_basis
        pnl_pct = (pnl / cost_basis * 100) if cost_basis != 0 else 0
        
        return {
            'symbol': symbol,
            'shares': holding['shares'],
            'avg_price': holding['avg_price'],
            'current_price': holding['current_price'],
            'cost_basis': cost_basis,
            'current_value': current_value,
            'pnl': pnl,
            'pnl_percent': pnl_pct,
            'entry_time': holding.get('entry_time')
        }
    
    def get_total_value(self) -> float:
        """
        Get total portfolio value (cash + holdings).
        
        Returns:
            Total portfolio value
        """
        holdings_value = sum(
            holding['shares'] * holding['current_price']
            for holding in self.holdings.values()
        )
        return self.cash + holdings_value
    
    def get_total_pnl(self) -> Dict:
        """
        Get total portfolio P&L.
        
        Returns:
            Dictionary with total P&L metrics
        """
        total_value = self.get_total_value()
        total_pnl = total_value - self.initial_capital
        pnl_pct = (total_pnl / self.initial_capital * 100) if self.initial_capital != 0 else 0
        
        return {
            'initial_capital': self.initial_capital,
            'current_value': total_value,
            'cash': self.cash,
            'holdings_value': total_value - self.cash,
            'total_pnl': total_pnl,
            'pnl_percent': pnl_pct
        }
    
    def get_all_positions(self) -> List[Dict]:
        """
        Get all open positions with P&L.
        
        Returns:
            List of position dictionaries
        """
        positions = []
        for symbol in self.holdings.keys():
            positions.append(self.get_position_pnl(symbol))
        return positions
    
    def get_trade_history(self) -> pd.DataFrame:
        """
        Get trade history as DataFrame.
        
        Returns:
            DataFrame of all trades
        """
        if not self.trades:
            return pd.DataFrame()
        return pd.DataFrame(self.trades)
    
    def reset(self):
        """
        Reset portfolio to initial state."""
        self.cash = self.initial_capital
        self.holdings.clear()
        self.trades.clear()
        self.performance_history.clear()
        logger.info("Portfolio reset")
