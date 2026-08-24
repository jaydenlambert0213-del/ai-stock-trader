"""Unit tests for Portfolio module."""

import pytest
from src.portfolio import Portfolio


class TestPortfolio:
    """Test suite for Portfolio class."""
    
    @pytest.fixture
    def portfolio(self):
        """Create a sample portfolio."""
        return Portfolio(initial_capital=100000)
    
    def test_portfolio_initialization(self, portfolio):
        """Test portfolio initialization."""
        assert portfolio.initial_capital == 100000
        assert portfolio.cash == 100000
        assert len(portfolio.holdings) == 0
    
    def test_buy_trade(self, portfolio):
        """Test buy trade execution."""
        result = portfolio.buy('AAPL', 100, 150.0)
        
        assert result is True
        assert 'AAPL' in portfolio.holdings
        assert portfolio.holdings['AAPL']['shares'] == 100
        assert portfolio.holdings['AAPL']['avg_price'] == 150.0
        assert portfolio.cash == 85000  # 100000 - (100 * 150)
    
    def test_sell_trade(self, portfolio):
        """Test sell trade execution."""
        portfolio.buy('AAPL', 100, 150.0)
        result = portfolio.sell('AAPL', 50, 160.0)
        
        assert result is True
        assert portfolio.holdings['AAPL']['shares'] == 50
        assert portfolio.cash == 92000  # 85000 + (50 * 160)
    
    def test_insufficient_cash(self, portfolio):
        """Test buying with insufficient cash."""
        result = portfolio.buy('AAPL', 1000, 150.0)  # Would cost 150,000
        
        assert result is False
        assert 'AAPL' not in portfolio.holdings
    
    def test_insufficient_shares(self, portfolio):
        """Test selling more shares than held."""
        portfolio.buy('AAPL', 100, 150.0)
        result = portfolio.sell('AAPL', 150, 160.0)
        
        assert result is False
        assert portfolio.holdings['AAPL']['shares'] == 100
    
    def test_position_pnl(self, portfolio):
        """Test P&L calculation for a position."""
        portfolio.buy('AAPL', 100, 150.0)
        portfolio.update_price('AAPL', 160.0)
        
        pnl = portfolio.get_position_pnl('AAPL')
        
        assert pnl['pnl'] == 1000  # (160 - 150) * 100
        assert pnl['pnl_percent'] == pytest.approx(6.67, rel=0.1)
    
    def test_total_value(self, portfolio):
        """Test total portfolio value calculation."""
        portfolio.buy('AAPL', 100, 150.0)
        portfolio.update_price('AAPL', 160.0)
        
        total = portfolio.get_total_value()
        expected = 85000 + (100 * 160)  # cash + holdings
        
        assert total == expected
    
    def test_reset_portfolio(self, portfolio):
        """Test portfolio reset."""
        portfolio.buy('AAPL', 100, 150.0)
        portfolio.reset()
        
        assert portfolio.cash == 100000
        assert len(portfolio.holdings) == 0
        assert len(portfolio.trades) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
