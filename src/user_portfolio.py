"""User-Specific Portfolio Management - Handles individual user portfolios."""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UserPortfolio:
    """Manages portfolio for a specific user."""
    
    def __init__(self, username: str, initial_capital: float = 10000.0, data_dir: str = 'data'):
        """
        Initialize user portfolio.
        
        Args:
            username: Username
            initial_capital: Initial capital
            data_dir: Directory to store portfolio data
        """
        self.username = username
        self.initial_capital = initial_capital
        self.data_dir = os.path.join(data_dir, 'portfolios')
        self.portfolio_file = os.path.join(self.data_dir, f'{username}_portfolio.json')
        self.trades_file = os.path.join(self.data_dir, f'{username}_trades.json')
        
        # Create directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load or initialize portfolio
        self.portfolio_data = self._load_portfolio()
        self.trades = self._load_trades()
    
    def _load_portfolio(self) -> Dict:
        """Load portfolio from file."""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading portfolio for {self.username}: {e}")
        
        return {
            'username': self.username,
            'initial_capital': self.initial_capital,
            'cash': self.initial_capital,
            'holdings': {},
            'performance_history': [],
            'created_at': datetime.now().isoformat()
        }
    
    def _load_trades(self) -> List:
        """Load trade history from file."""
        if os.path.exists(self.trades_file):
            try:
                with open(self.trades_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading trades for {self.username}: {e}")
        return []
    
    def _save_portfolio(self):
        """Save portfolio to file."""
        try:
            with open(self.portfolio_file, 'w') as f:
                json.dump(self.portfolio_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving portfolio for {self.username}: {e}")
    
    def _save_trades(self):
        """Save trades to file."""
        try:
            with open(self.trades_file, 'w') as f:
                json.dump(self.trades, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving trades for {self.username}: {e}")
    
    @property
    def cash(self) -> float:
        """Get available cash."""
        return self.portfolio_data['cash']
    
    @cash.setter
    def cash(self, value: float):
        """Set cash amount."""
        self.portfolio_data['cash'] = value
        self._save_portfolio()
    
    @property
    def holdings(self) -> Dict:
        """Get current holdings."""
        return self.portfolio_data['holdings']
    
    @property
    def performance_history(self) -> List:
        """Get performance history."""
        return self.portfolio_data['performance_history']
    
    def buy(self, symbol: str, shares: float, price: float, commission: float = 0.0) -> bool:
        """
        Execute buy trade.
        
        Args:
            symbol: Stock symbol
            shares: Number of shares
            price: Price per share
            commission: Commission amount
            
        Returns:
            True if successful
        """
        total_cost = (shares * price) + commission
        
        if self.cash < total_cost:
            logger.warning(f"{self.username}: Insufficient cash for {symbol} buy")
            return False
        
        self.cash -= total_cost
        
        if symbol in self.holdings:
            holding = self.holdings[symbol]
            old_avg = holding['avg_price']
            old_shares = holding['shares']
            
            # Calculate new average price
            holding['avg_price'] = ((old_avg * old_shares) + (price * shares)) / (old_shares + shares)
            holding['shares'] += shares
        else:
            self.holdings[symbol] = {
                'shares': shares,
                'avg_price': price,
                'current_price': price
            }
        
        # Record trade
        self.trades.append({
            'type': 'BUY',
            'symbol': symbol,
            'shares': shares,
            'price': price,
            'total': total_cost,
            'timestamp': datetime.now().isoformat()
        })
        
        self._save_portfolio()
        self._save_trades()
        logger.info(f"{self.username}: Bought {shares} shares of {symbol} at ${price:.2f}")
        
        return True
    
    def sell(self, symbol: str, shares: float, price: float, commission: float = 0.0) -> bool:
        """
        Execute sell trade.
        
        Args:
            symbol: Stock symbol
            shares: Number of shares
            price: Price per share
            commission: Commission amount
            
        Returns:
            True if successful
        """
        if symbol not in self.holdings:
            logger.warning(f"{self.username}: No position in {symbol}")
            return False
        
        holding = self.holdings[symbol]
        if holding['shares'] < shares:
            logger.warning(f"{self.username}: Insufficient shares of {symbol}")
            return False
        
        proceeds = (shares * price) - commission
        self.cash += proceeds
        
        holding['shares'] -= shares
        
        if holding['shares'] == 0:
            del self.holdings[symbol]
        
        # Record trade
        self.trades.append({
            'type': 'SELL',
            'symbol': symbol,
            'shares': shares,
            'price': price,
            'total': proceeds,
            'timestamp': datetime.now().isoformat()
        })
        
        self._save_portfolio()
        self._save_trades()
        logger.info(f"{self.username}: Sold {shares} shares of {symbol} at ${price:.2f}")
        
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
            self._save_portfolio()
    
    def get_total_pnl(self) -> Dict:
        """
        Calculate total P&L.
        
        Returns:
            Dictionary with P&L metrics
        """
        holdings_value = 0.0
        
        for symbol, holding in self.holdings.items():
            current_value = holding['shares'] * holding['current_price']
            holdings_value += current_value
        
        current_value = self.cash + holdings_value
        total_pnl = current_value - self.initial_capital
        pnl_percent = (total_pnl / self.initial_capital * 100) if self.initial_capital > 0 else 0
        
        return {
            'current_value': current_value,
            'cash': self.cash,
            'holdings_value': holdings_value,
            'total_pnl': total_pnl,
            'pnl_percent': pnl_percent
        }
    
    def get_all_positions(self) -> List[Dict]:
        """
        Get all current positions.
        
        Returns:
            List of position dictionaries
        """
        positions = []
        
        for symbol, holding in self.holdings.items():
            current_value = holding['shares'] * holding['current_price']
            pnl = current_value - (holding['shares'] * holding['avg_price'])
            pnl_percent = (pnl / (holding['shares'] * holding['avg_price']) * 100) if (holding['shares'] * holding['avg_price']) > 0 else 0
            
            positions.append({
                'symbol': symbol,
                'shares': holding['shares'],
                'avg_price': holding['avg_price'],
                'current_price': holding['current_price'],
                'current_value': current_value,
                'pnl': pnl,
                'pnl_percent': pnl_percent
            })
        
        return positions
    
    def get_trade_history(self) -> List[Dict]:
        """
        Get trade history.
        
        Returns:
            List of trades
        """
        return self.trades
    
    def get_holding(self, symbol: str) -> Optional[Dict]:
        """
        Get specific holding.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Holding dictionary or None
        """
        return self.holdings.get(symbol)
    
    def to_dict(self) -> Dict:
        """Get portfolio as dictionary."""
        return self.portfolio_data
