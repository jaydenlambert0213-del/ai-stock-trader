"""Unit tests for AI Engine module."""

import pytest
import pandas as pd
import numpy as np
from src.ai_engine import AIEngine
from src.indicators import TechnicalIndicators


class TestAIEngine:
    """Test suite for AIEngine class."""
    
    @pytest.fixture
    def config(self):
        """Create sample configuration."""
        return {
            'indicators': {
                'rsi_period': 14,
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'bollinger_period': 20,
                'bollinger_std': 2,
            },
            'ai_engine': {
                'min_confidence': 0.6,
                'trend_threshold': 0.55,
            }
        }
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create sample OHLCV data with indicators."""
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        
        df = pd.DataFrame({
            'Date': dates,
            'Open': np.linspace(100, 110, 100) + np.random.normal(0, 0.5, 100),
            'High': np.linspace(101, 111, 100) + np.random.normal(0, 0.5, 100),
            'Low': np.linspace(99, 109, 100) + np.random.normal(0, 0.5, 100),
            'Close': np.linspace(100, 110, 100) + np.random.normal(0, 0.5, 100),
            'Volume': np.random.randint(1000000, 5000000, 100),
        })
        
        # Add indicators
        df['RSI'] = TechnicalIndicators.calculate_rsi(df['Close'], 14)
        df['MACD'], df['MACD_Signal'], df['MACD_Histogram'] = TechnicalIndicators.calculate_macd(df['Close'])
        df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = TechnicalIndicators.calculate_bollinger_bands(df['Close'])
        df['SMA_20'] = TechnicalIndicators.calculate_sma(df['Close'], 20)
        df['SMA_50'] = TechnicalIndicators.calculate_sma(df['Close'], 50)
        df['EMA_12'] = TechnicalIndicators.calculate_ema(df['Close'], 12)
        df['Volume_SMA'] = df['Volume'].rolling(20).mean()
        
        return df
    
    def test_ai_engine_initialization(self, config):
        """Test AI Engine initialization."""
        engine = AIEngine(config)
        assert engine.min_confidence == 0.6
        assert engine.trend_threshold == 0.55
    
    def test_analyze_stock(self, config, sample_dataframe):
        """Test stock analysis."""
        engine = AIEngine(config)
        analysis = engine.analyze_stock(sample_dataframe, 'TEST')
        
        assert analysis['symbol'] == 'TEST'
        assert 'recommendation' in analysis
        assert 'confidence' in analysis
        assert 'signals' in analysis
        assert 'scores' in analysis
        assert analysis['recommendation'] in ['BUY', 'SELL', 'HOLD']
    
    def test_insufficient_data(self, config):
        """Test handling of insufficient data."""
        engine = AIEngine(config)
        
        # Create small dataframe
        small_df = pd.DataFrame({
            'Close': [100, 101, 102],
        })
        
        analysis = engine.analyze_stock(small_df, 'TEST')
        assert analysis['recommendation'] == 'HOLD'
        assert analysis['confidence'] == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
