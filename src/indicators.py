"""Technical indicators calculation module."""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Calculate technical indicators for price and volume data."""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).
        
        Args:
            prices: Series of closing prices
            period: Period for RSI calculation
            
        Returns:
            Series of RSI values
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: Series of closing prices
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line EMA period
            
        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: Series of closing prices
            period: Period for moving average
            std_dev: Number of standard deviations
            
        Returns:
            Tuple of (Upper band, Middle band, Lower band)
        """
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper, middle, lower
    
    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Simple Moving Average (SMA).
        
        Args:
            prices: Series of closing prices
            period: Period for SMA
            
        Returns:
            Series of SMA values
        """
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average (EMA).
        
        Args:
            prices: Series of closing prices
            period: Period for EMA
            
        Returns:
            Series of EMA values
        """
        return prices.ewm(span=period).mean()
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR) for volatility measurement.
        
        Args:
            df: DataFrame with 'High', 'Low', 'Close' columns
            period: ATR period
            
        Returns:
            Series of ATR values
        """
        tr1 = df['High'] - df['Low']
        tr2 = abs(df['High'] - df['Close'].shift())
        tr3 = abs(df['Low'] - df['Close'].shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def calculate_volume_sma(volume: pd.Series, period: int = 20) -> pd.Series:
        """
        Calculate Volume SMA for volume analysis.
        
        Args:
            volume: Series of volumes
            period: Period for SMA
            
        Returns:
            Series of volume SMA values
        """
        return volume.rolling(window=period).mean()
    
    @staticmethod
    def calculate_obv(df: pd.DataFrame) -> pd.Series:
        """
        Calculate On-Balance Volume (OBV).
        
        Args:
            df: DataFrame with 'Close' and 'Volume' columns
            
        Returns:
            Series of OBV values
        """
        obv = [0]
        for i in range(1, len(df)):
            if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
                obv.append(obv[-1] + df['Volume'].iloc[i])
            elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
                obv.append(obv[-1] - df['Volume'].iloc[i])
            else:
                obv.append(obv[-1])
        
        return pd.Series(obv, index=df.index)
    
    @staticmethod
    def calculate_roc(prices: pd.Series, period: int = 12) -> pd.Series:
        """
        Calculate Rate of Change (ROC).
        
        Args:
            prices: Series of prices
            period: ROC period
            
        Returns:
            Series of ROC values
        """
        return ((prices - prices.shift(period)) / prices.shift(period)) * 100
    
    @staticmethod
    def calculate_stochastic(df: pd.DataFrame, period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic Oscillator.
        
        Args:
            df: DataFrame with 'High', 'Low', 'Close' columns
            period: Stochastic period
            smooth_k: K smoothing period
            smooth_d: D smoothing period
            
        Returns:
            Tuple of (K line, D line)
        """
        low_min = df['Low'].rolling(window=period).min()
        high_max = df['High'].rolling(window=period).max()
        
        k_percent = 100 * ((df['Close'] - low_min) / (high_max - low_min))
        k_line = k_percent.rolling(window=smooth_k).mean()
        d_line = k_line.rolling(window=smooth_d).mean()
        
        return k_line, d_line
    
    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame, config: Dict) -> pd.DataFrame:
        """
        Calculate all technical indicators.
        
        Args:
            df: DataFrame with OHLCV data
            config: Configuration dictionary with indicator parameters
            
        Returns:
            DataFrame with all indicators added
        """
        df = df.copy()
        indicators = config.get('indicators', {})
        
        try:
            # RSI
            df['RSI'] = TechnicalIndicators.calculate_rsi(
                df['Close'],
                period=indicators.get('rsi_period', 14)
            )
            
            # MACD
            df['MACD'], df['MACD_Signal'], df['MACD_Histogram'] = TechnicalIndicators.calculate_macd(
                df['Close'],
                fast=indicators.get('macd_fast', 12),
                slow=indicators.get('macd_slow', 26),
                signal=indicators.get('macd_signal', 9)
            )
            
            # Bollinger Bands
            df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = TechnicalIndicators.calculate_bollinger_bands(
                df['Close'],
                period=indicators.get('bollinger_period', 20),
                std_dev=indicators.get('bollinger_std', 2)
            )
            
            # Moving Averages
            df['SMA_20'] = TechnicalIndicators.calculate_sma(df['Close'], 20)
            df['SMA_50'] = TechnicalIndicators.calculate_sma(df['Close'], 50)
            df['EMA_12'] = TechnicalIndicators.calculate_ema(df['Close'], 12)
            
            # ATR for volatility
            df['ATR'] = TechnicalIndicators.calculate_atr(df, period=14)
            
            # Volume indicators
            df['Volume_SMA'] = TechnicalIndicators.calculate_volume_sma(df['Volume'], 20)
            df['OBV'] = TechnicalIndicators.calculate_obv(df)
            
            # ROC
            df['ROC'] = TechnicalIndicators.calculate_roc(df['Close'], 12)
            
            # Stochastic
            df['Stoch_K'], df['Stoch_D'] = TechnicalIndicators.calculate_stochastic(df)
            
            logger.info(f"Calculated all indicators for {len(df)} records")
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
        
        return df
