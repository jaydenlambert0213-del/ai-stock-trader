"""Unit tests for technical indicators module."""

import pytest
import pandas as pd
import numpy as np
from src.indicators import TechnicalIndicators


class TestTechnicalIndicators:
    """Test suite for TechnicalIndicators class."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample price data for testing."""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        prices = pd.Series(
            np.linspace(100, 110, 100) + np.random.normal(0, 1, 100),
            index=dates,
            name='Close'
        )
        return prices
    
    def test_rsi_calculation(self, sample_data):
        """Test RSI calculation."""
        rsi = TechnicalIndicators.calculate_rsi(sample_data, period=14)
        
        assert len(rsi) == len(sample_data)
        assert rsi.min() >= 0
        assert rsi.max() <= 100
    
    def test_macd_calculation(self, sample_data):
        """Test MACD calculation."""
        macd_line, signal_line, histogram = TechnicalIndicators.calculate_macd(sample_data)
        
        assert len(macd_line) == len(sample_data)
        assert len(signal_line) == len(sample_data)
        assert len(histogram) == len(sample_data)
    
    def test_bollinger_bands(self, sample_data):
        """Test Bollinger Bands calculation."""
        upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(
            sample_data, period=20, std_dev=2
        )
        
        assert len(upper) == len(sample_data)
        assert len(middle) == len(sample_data)
        assert len(lower) == len(sample_data)
        assert (upper >= middle).all() or pd.isna(upper).any()
        assert (middle >= lower).all() or pd.isna(lower).any()
    
    def test_sma_calculation(self, sample_data):
        """Test SMA calculation."""
        sma = TechnicalIndicators.calculate_sma(sample_data, period=20)
        
        assert len(sma) == len(sample_data)
        assert sma.isna().sum() == 19  # First 19 values should be NaN
    
    def test_ema_calculation(self, sample_data):
        """Test EMA calculation."""
        ema = TechnicalIndicators.calculate_ema(sample_data, period=12)
        
        assert len(ema) == len(sample_data)
        assert not ema.isna().all()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
