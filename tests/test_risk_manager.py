"""Unit tests for Risk Manager module."""

import pytest
from src.risk_manager import RiskManager


class TestRiskManager:
    """Test suite for RiskManager class."""
    
    @pytest.fixture
    def config(self):
        """Create sample configuration."""
        return {
            'trading': {
                'max_position_size': 0.05,
                'stop_loss_percent': 2.0,
                'daily_loss_limit': 5.0,
            },
            'risk_management': {
                'use_trailing_stop': True,
                'trailing_stop_percent': 1.5,
                'take_profit_percent': 5.0,
                'max_positions': 5,
                'min_risk_reward': 1.5,
            }
        }
    
    @pytest.fixture
    def risk_manager(self, config):
        """Create a risk manager instance."""
        return RiskManager(config)
    
    def test_risk_manager_initialization(self, risk_manager):
        """Test risk manager initialization."""
        assert risk_manager.max_position_size == 0.05
        assert risk_manager.stop_loss_percent == 2.0
        assert risk_manager.daily_loss_limit == 5.0
    
    def test_validate_buy_trade_sufficient_cash(self, risk_manager):
        """Test buy trade validation with sufficient cash."""
        valid, reason = risk_manager.validate_buy_trade(
            'AAPL', 100, 150.0, 100000, 100000, 0
        )
        
        assert valid is True
    
    def test_validate_buy_trade_insufficient_cash(self, risk_manager):
        """Test buy trade validation with insufficient cash."""
        valid, reason = risk_manager.validate_buy_trade(
            'AAPL', 1000, 150.0, 100000, 50000, 0
        )
        
        assert valid is False
    
    def test_validate_buy_trade_position_size_limit(self, risk_manager):
        """Test position size limit validation."""
        valid, reason = risk_manager.validate_buy_trade(
            'AAPL', 1000, 100.0, 100000, 100000, 0
        )
        
        assert valid is False
    
    def test_validate_buy_trade_max_positions(self, risk_manager):
        """Test maximum positions limit."""
        valid, reason = risk_manager.validate_buy_trade(
            'AAPL', 10, 150.0, 100000, 100000, 5
        )
        
        assert valid is False
    
    def test_calculate_stop_loss_buy(self, risk_manager):
        """Test stop loss calculation for buy trade."""
        stop_loss = risk_manager.calculate_stop_loss(100.0, 'BUY')
        expected = 100.0 * (1 - 0.02)  # 2% stop loss
        
        assert stop_loss == pytest.approx(expected)
    
    def test_calculate_stop_loss_sell(self, risk_manager):
        """Test stop loss calculation for sell trade."""
        stop_loss = risk_manager.calculate_stop_loss(100.0, 'SELL')
        expected = 100.0 * (1 + 0.02)  # 2% stop loss
        
        assert stop_loss == pytest.approx(expected)
    
    def test_calculate_take_profit_buy(self, risk_manager):
        """Test take profit calculation for buy trade."""
        take_profit = risk_manager.calculate_take_profit(100.0, 'BUY')
        expected = 100.0 * (1 + 0.05)  # 5% take profit
        
        assert take_profit == pytest.approx(expected)
    
    def test_check_stop_loss_hit_buy(self, risk_manager):
        """Test stop loss hit detection for buy trade."""
        entry_price = 100.0
        current_price = 97.5  # Below 98.0 stop loss
        
        hit = risk_manager.check_stop_loss_hit(current_price, entry_price, 'BUY')
        assert hit is True
    
    def test_check_take_profit_hit_buy(self, risk_manager):
        """Test take profit hit detection for buy trade."""
        entry_price = 100.0
        current_price = 105.5  # Above 105.0 take profit
        
        hit = risk_manager.check_take_profit_hit(current_price, entry_price, 'BUY')
        assert hit is True
    
    def test_daily_loss_tracking(self, risk_manager):
        """Test daily loss tracking."""
        risk_manager.update_daily_loss(2.0)
        assert risk_manager.daily_loss == 2.0
        
        risk_manager.update_daily_loss(1.5)
        assert risk_manager.daily_loss == 3.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
