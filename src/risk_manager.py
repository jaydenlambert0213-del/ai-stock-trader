"""Risk Management Module - Controls and validates trades."""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)


class RiskManager:
    """Manages risk controls and trade validation."""
    
    def __init__(self, config: Dict):
        """
        Initialize Risk Manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.trading_config = config.get('trading', {})
        self.risk_config = config.get('risk_management', {})
        
        # Risk parameters
        self.max_position_size = self.trading_config.get('max_position_size', 0.05)
        self.stop_loss_percent = self.trading_config.get('stop_loss_percent', 2.0)
        self.daily_loss_limit = self.trading_config.get('daily_loss_limit', 5.0)
        self.use_trailing_stop = self.risk_config.get('use_trailing_stop', True)
        self.trailing_stop_percent = self.risk_config.get('trailing_stop_percent', 1.5)
        self.take_profit_percent = self.risk_config.get('take_profit_percent', 5.0)
        self.max_positions = self.risk_config.get('max_positions', 5)
        self.min_risk_reward = self.risk_config.get('min_risk_reward', 1.5)
        
        # Daily tracking
        self.daily_loss = 0.0
        self.daily_date = date.today()
        self.daily_trades = []
    
    def validate_buy_trade(self, symbol: str, shares: float, price: float, 
                          portfolio_value: float, cash: float, 
                          num_open_positions: int) -> Tuple[bool, str]:
        """
        Validate a buy trade against risk parameters.
        
        Args:
            symbol: Stock symbol
            shares: Number of shares to buy
            price: Price per share
            portfolio_value: Total portfolio value
            cash: Available cash
            num_open_positions: Number of currently open positions
            
        Returns:
            Tuple of (is_valid, reason)
        """
        cost = shares * price
        
        # Check 1: Sufficient cash
        if cash < cost:
            return False, f"Insufficient cash: need ${cost:.2f}, have ${cash:.2f}"
        
        # Check 2: Position size limit
        position_size_pct = (cost / portfolio_value) * 100
        if position_size_pct > (self.max_position_size * 100):
            return False, f"Position size {position_size_pct:.2f}% exceeds limit {self.max_position_size*100:.2f}%"
        
        # Check 3: Maximum positions
        if num_open_positions >= self.max_positions:
            return False, f"Already have {num_open_positions} open positions (max: {self.max_positions})"
        
        # Check 4: Daily loss limit
        if self._check_daily_loss_limit():
            return False, f"Daily loss limit (${self.daily_loss_limit}%) exceeded. Daily loss: ${self.daily_loss:.2f}"
        
        return True, "Trade validated"
    
    def validate_sell_trade(self, symbol: str, shares: float, current_price: float,
                           entry_price: float, current_profit_loss: float) -> Tuple[bool, str]:
        """
        Validate a sell trade.
        
        Args:
            symbol: Stock symbol
            shares: Number of shares to sell
            current_price: Current price
            entry_price: Entry price
            current_profit_loss: Current P&L
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Sell is generally allowed if position exists
        return True, "Sell trade validated"
    
    def calculate_position_size(self, portfolio_value: float, symbol: str,
                               entry_price: float, stop_loss_price: float) -> float:
        """
        Calculate optimal position size based on risk.
        
        Args:
            portfolio_value: Total portfolio value
            symbol: Stock symbol
            entry_price: Entry price
            stop_loss_price: Stop loss price
            
        Returns:
            Number of shares to buy
        """
        risk_per_trade = portfolio_value * (self.max_position_size / self.max_positions)
        price_risk = abs(entry_price - stop_loss_price)
        
        if price_risk == 0:
            shares = risk_per_trade / entry_price
        else:
            shares = risk_per_trade / price_risk
        
        return max(1, int(shares))
    
    def calculate_stop_loss(self, entry_price: float, trade_type: str = 'BUY') -> float:
        """
        Calculate stop loss price.
        
        Args:
            entry_price: Entry price
            trade_type: 'BUY' or 'SELL'
            
        Returns:
            Stop loss price
        """
        if trade_type == 'BUY':
            return entry_price * (1 - self.stop_loss_percent / 100)
        else:
            return entry_price * (1 + self.stop_loss_percent / 100)
    
    def calculate_take_profit(self, entry_price: float, trade_type: str = 'BUY') -> float:
        """
        Calculate take profit price.
        
        Args:
            entry_price: Entry price
            trade_type: 'BUY' or 'SELL'
            
        Returns:
            Take profit price
        """
        if trade_type == 'BUY':
            return entry_price * (1 + self.take_profit_percent / 100)
        else:
            return entry_price * (1 - self.take_profit_percent / 100)
    
    def check_stop_loss_hit(self, current_price: float, entry_price: float,
                           trade_type: str = 'BUY') -> bool:
        """
        Check if stop loss has been hit.
        
        Args:
            current_price: Current price
            entry_price: Entry price
            trade_type: 'BUY' or 'SELL'
            
        Returns:
            True if stop loss hit
        """
        stop_loss = self.calculate_stop_loss(entry_price, trade_type)
        
        if trade_type == 'BUY':
            return current_price <= stop_loss
        else:
            return current_price >= stop_loss
    
    def check_take_profit_hit(self, current_price: float, entry_price: float,
                             trade_type: str = 'BUY') -> bool:
        """
        Check if take profit has been hit.
        
        Args:
            current_price: Current price
            entry_price: Entry price
            trade_type: 'BUY' or 'SELL'
            
        Returns:
            True if take profit hit
        """
        take_profit = self.calculate_take_profit(entry_price, trade_type)
        
        if trade_type == 'BUY':
            return current_price >= take_profit
        else:
            return current_price <= take_profit
    
    def calculate_trailing_stop(self, highest_price: float, trade_type: str = 'BUY') -> float:
        """
        Calculate trailing stop price.
        
        Args:
            highest_price: Highest price since entry (for BUY) or lowest (for SELL)
            trade_type: 'BUY' or 'SELL'
            
        Returns:
            Trailing stop price
        """
        if trade_type == 'BUY':
            return highest_price * (1 - self.trailing_stop_percent / 100)
        else:
            return highest_price * (1 + self.trailing_stop_percent / 100)
    
    def check_daily_loss_limit(self) -> bool:
        """
        Check if daily loss limit has been exceeded.
        
        Returns:
            True if daily loss limit exceeded
        """
        return self.daily_loss > self.daily_loss_limit
    
    def update_daily_loss(self, loss_amount: float):
        """
        Update daily loss tracking.
        
        Args:
            loss_amount: Amount lost on trade
        """
        current_date = date.today()
        
        # Reset if new day
        if current_date != self.daily_date:
            self.daily_loss = 0.0
            self.daily_date = current_date
            self.daily_trades = []
        
        if loss_amount > 0:
            self.daily_loss += loss_amount
            logger.info(f"Daily loss updated: ${self.daily_loss:.2f}")
    
    def record_trade(self, trade_info: Dict):
        """
        Record a trade for daily tracking.
        
        Args:
            trade_info: Dictionary with trade information
        """
        current_date = date.today()
        
        if current_date != self.daily_date:
            self.daily_trades = []
            self.daily_date = current_date
        
        self.daily_trades.append(trade_info)
    
    def get_risk_report(self) -> Dict:
        """
        Get current risk status report.
        
        Returns:
            Risk report dictionary
        """
        daily_loss_pct = (self.daily_loss / self.daily_loss_limit) * 100 if self.daily_loss_limit > 0 else 0
        
        return {
            'daily_loss': self.daily_loss,
            'daily_loss_limit': self.daily_loss_limit,
            'daily_loss_percent': daily_loss_pct,
            'daily_trades_count': len(self.daily_trades),
            'max_position_size_percent': self.max_position_size * 100,
            'stop_loss_percent': self.stop_loss_percent,
            'take_profit_percent': self.take_profit_percent,
            'max_positions': self.max_positions,
            'trading_enabled': not self._check_daily_loss_limit()
        }
