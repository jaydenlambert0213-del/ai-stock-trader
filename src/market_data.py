"""Market data fetching and preprocessing module."""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MarketData:
    """Handles market data fetching and preprocessing from Yahoo Finance."""
    
    def __init__(self, symbols: List[str], interval: str = '1d'):
        """
        Initialize MarketData handler.
        
        Args:
            symbols: List of stock symbols to track
            interval: Data interval ('1d', '1h', '15m', etc.)
        """
        self.symbols = symbols
        self.interval = interval
        self.data_cache = {}
        self.last_update = {}
        
    def fetch_data(self, symbol: str, period: str = '1y') -> Optional[pd.DataFrame]:
        """
        Fetch historical data for a symbol.
        
        Args:
            symbol: Stock symbol
            period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max')
            
        Returns:
            DataFrame with OHLCV data or None if fetch fails
        """
        try:
            logger.info(f"Fetching data for {symbol} ({period})")
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=self.interval)
            
            if df.empty:
                logger.warning(f"No data retrieved for {symbol}")
                return None
            
            df = df.reset_index()
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            df['Symbol'] = symbol
            
            self.data_cache[symbol] = df
            self.last_update[symbol] = datetime.now()
            
            logger.info(f"Successfully fetched {len(df)} rows for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Get the latest closing price for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Latest closing price or None
        """
        try:
            ticker = yf.Ticker(symbol)
            return ticker.info.get('currentPrice') or ticker.history(period='1d')['Close'].iloc[-1]
        except Exception as e:
            logger.error(f"Error getting latest price for {symbol}: {str(e)}")
            return None
    
    def get_current_data(self, symbols: List[str]) -> pd.DataFrame:
        """
        Get current data for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            DataFrame with current data for all symbols
        """
        current_data = []
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                current_data.append({
                    'Symbol': symbol,
                    'Price': info.get('currentPrice', 0),
                    'Open': info.get('open', 0),
                    'High': info.get('dayHigh', 0),
                    'Low': info.get('dayLow', 0),
                    'Volume': info.get('volume', 0),
                    'MarketCap': info.get('marketCap', 0),
                    'PEatio': info.get('trailingPE', 0),
                    'Change': info.get('regularMarketChange', 0),
                    'ChangePercent': info.get('regularMarketChangePercent', 0),
                })
            except Exception as e:
                logger.error(f"Error getting current data for {symbol}: {str(e)}")
        
        return pd.DataFrame(current_data) if current_data else pd.DataFrame()
    
    def calculate_returns(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate daily returns from price data.
        
        Args:
            df: DataFrame with 'Close' column
            
        Returns:
            Series of daily returns
        """
        return df['Close'].pct_change()
    
    def calculate_log_returns(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate log returns from price data.
        
        Args:
            df: DataFrame with 'Close' column
            
        Returns:
            Series of log returns
        """
        return np.log(df['Close'] / df['Close'].shift(1))
    
    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess OHLCV data.
        
        Args:
            df: Raw OHLCV DataFrame
            
        Returns:
            Preprocessed DataFrame
        """
        df = df.copy()
        
        # Handle missing values
        df = df.dropna()
        
        # Calculate returns
        df['Returns'] = df['Close'].pct_change()
        df['LogReturns'] = np.log(df['Close'] / df['Close'].shift(1))
        
        # Calculate price changes
        df['DayChange'] = df['Close'] - df['Open']
        df['HighLowRange'] = df['High'] - df['Low']
        
        # Volume calculations
        df['AvgVolume'] = df['Volume'].rolling(window=20).mean()
        df['VolumeRatio'] = df['Volume'] / df['AvgVolume']
        
        return df
    
    def get_cached_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Get cached data for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Cached DataFrame or None
        """
        return self.data_cache.get(symbol)
    
    def clear_cache(self):
        """Clear all cached data."""
        self.data_cache.clear()
        self.last_update.clear()
        logger.info("Cleared data cache")
