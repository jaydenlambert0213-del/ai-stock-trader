"""AI Trading Engine - Core decision-making logic."""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AIEngine:
    """AI-driven trading signal generation and decision making."""
    
    def __init__(self, config: Dict):
        """
        Initialize AI Engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.ai_config = config.get('ai_engine', {})
        self.indicator_config = config.get('indicators', {})
        self.min_confidence = self.ai_config.get('min_confidence', 0.6)
        self.trend_threshold = self.ai_config.get('trend_threshold', 0.55)
        
    def analyze_stock(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Analyze a stock and generate trading signals.
        
        Args:
            df: DataFrame with OHLCV and indicator data
            symbol: Stock symbol
            
        Returns:
            Dictionary with analysis results and signals
        """
        if df.empty or len(df) < 30:
            logger.warning(f"Insufficient data for {symbol}")
            return self._empty_analysis(symbol)
        
        latest = df.iloc[-1]
        analysis = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'price': latest['Close'],
            'signals': {},
            'scores': {},
            'recommendation': 'HOLD',
            'confidence': 0.0,
            'reason': 'Insufficient signal strength'
        }
        
        # RSI Analysis
        rsi_signal, rsi_score = self._analyze_rsi(latest, df)
        analysis['signals']['RSI'] = rsi_signal
        analysis['scores']['RSI'] = rsi_score
        
        # MACD Analysis
        macd_signal, macd_score = self._analyze_macd(latest, df)
        analysis['signals']['MACD'] = macd_signal
        analysis['scores']['MACD'] = macd_score
        
        # Bollinger Bands Analysis
        bb_signal, bb_score = self._analyze_bollinger_bands(latest, df)
        analysis['signals']['BollingerBands'] = bb_signal
        analysis['scores']['BollingerBands'] = bb_score
        
        # Moving Average Analysis
        ma_signal, ma_score = self._analyze_moving_averages(latest, df)
        analysis['signals']['MovingAverages'] = ma_signal
        analysis['scores']['MovingAverages'] = ma_score
        
        # Trend Analysis
        trend_signal, trend_score = self._analyze_trend(df)
        analysis['signals']['Trend'] = trend_signal
        analysis['scores']['Trend'] = trend_score
        
        # Volume Analysis
        volume_signal, volume_score = self._analyze_volume(latest, df)
        analysis['signals']['Volume'] = volume_signal
        analysis['scores']['Volume'] = volume_score
        
        # Calculate overall recommendation
        analysis['recommendation'], analysis['confidence'] = self._generate_recommendation(analysis['scores'])
        analysis['reason'] = self._generate_reason(analysis['signals'], analysis['recommendation'])
        
        return analysis
    
    def _analyze_rsi(self, latest, df) -> Tuple[str, float]:
        """
        Analyze RSI signal.
        
        Returns:
            Tuple of (signal, score)
        """
        try:
            rsi = latest['RSI']
            rsi_oversold = self.indicator_config.get('rsi_oversold', 30)
            rsi_overbought = self.indicator_config.get('rsi_overbought', 70)
            
            if pd.isna(rsi):
                return 'NEUTRAL', 0.5
            
            if rsi < rsi_oversold:
                return 'BUY', 0.8  # Oversold
            elif rsi > rsi_overbought:
                return 'SELL', 0.8  # Overbought
            elif rsi < 50:
                return 'BUY', 0.4
            else:
                return 'SELL', 0.4
        except Exception as e:
            logger.error(f"RSI analysis error: {e}")
            return 'NEUTRAL', 0.5
    
    def _analyze_macd(self, latest, df) -> Tuple[str, float]:
        """
        Analyze MACD signal.
        
        Returns:
            Tuple of (signal, score)
        """
        try:
            macd = latest['MACD']
            signal_line = latest['MACD_Signal']
            histogram = latest['MACD_Histogram']
            
            if pd.isna(macd) or pd.isna(signal_line):
                return 'NEUTRAL', 0.5
            
            # Look at last few bars for trend
            recent_histograms = df['MACD_Histogram'].tail(5).dropna()
            
            if len(recent_histograms) == 0:
                return 'NEUTRAL', 0.5
            
            if histogram > 0 and histogram > recent_histograms.iloc[-2] if len(recent_histograms) > 1 else True:
                return 'BUY', 0.7
            elif histogram < 0 and histogram < recent_histograms.iloc[-2] if len(recent_histograms) > 1 else True:
                return 'SELL', 0.7
            elif macd > signal_line:
                return 'BUY', 0.5
            else:
                return 'SELL', 0.5
        except Exception as e:
            logger.error(f"MACD analysis error: {e}")
            return 'NEUTRAL', 0.5
    
    def _analyze_bollinger_bands(self, latest, df) -> Tuple[str, float]:
        """
        Analyze Bollinger Bands signal.
        
        Returns:
            Tuple of (signal, score)
        """
        try:
            price = latest['Close']
            upper = latest['BB_Upper']
            lower = latest['BB_Lower']
            middle = latest['BB_Middle']
            
            if pd.isna(upper) or pd.isna(lower):
                return 'NEUTRAL', 0.5
            
            if price < lower:
                return 'BUY', 0.75  # Price hit lower band
            elif price > upper:
                return 'SELL', 0.75  # Price hit upper band
            elif price < middle:
                return 'BUY', 0.4
            else:
                return 'SELL', 0.4
        except Exception as e:
            logger.error(f"Bollinger Bands analysis error: {e}")
            return 'NEUTRAL', 0.5
    
    def _analyze_moving_averages(self, latest, df) -> Tuple[str, float]:
        """
        Analyze Moving Averages signal.
        
        Returns:
            Tuple of (signal, score)
        """
        try:
            price = latest['Close']
            sma20 = latest['SMA_20']
            sma50 = latest['SMA_50']
            ema12 = latest['EMA_12']
            
            if pd.isna(sma20) or pd.isna(sma50):
                return 'NEUTRAL', 0.5
            
            bullish_signals = 0
            
            if sma20 > sma50:
                bullish_signals += 1
            if price > sma20:
                bullish_signals += 0.5
            if price > sma50:
                bullish_signals += 0.5
            
            score = bullish_signals / 2.0
            
            if score > 0.7:
                return 'BUY', score
            elif score < 0.3:
                return 'SELL', 1 - score
            else:
                return 'NEUTRAL', 0.5
        except Exception as e:
            logger.error(f"Moving Averages analysis error: {e}")
            return 'NEUTRAL', 0.5
    
    def _analyze_trend(self, df) -> Tuple[str, float]:
        """
        Analyze overall trend.
        
        Returns:
            Tuple of (signal, score)
        """
        try:
            recent = df['Close'].tail(20)
            
            if len(recent) < 10:
                return 'NEUTRAL', 0.5
            
            # Calculate trend using linear regression
            x = np.arange(len(recent))
            y = recent.values
            
            # Simple trend calculation
            slope = (y[-1] - y[0]) / len(y)
            volatility = y.std()
            
            trend_strength = abs(slope) / volatility if volatility > 0 else 0
            
            if trend_strength > self.trend_threshold:
                if slope > 0:
                    return 'BUY', trend_strength
                else:
                    return 'SELL', trend_strength
            else:
                return 'NEUTRAL', 0.5
        except Exception as e:
            logger.error(f"Trend analysis error: {e}")
            return 'NEUTRAL', 0.5
    
    def _analyze_volume(self, latest, df) -> Tuple[str, float]:
        """
        Analyze volume signal.
        
        Returns:
            Tuple of (signal, score)
        """
        try:
            volume_ratio = latest['Volume'] / latest['Volume_SMA'] if 'Volume_SMA' in latest and latest['Volume_SMA'] > 0 else 1.0
            
            # High volume often confirms moves
            if volume_ratio > 1.5:
                # Check price direction
                if len(df) > 1:
                    price_change = df['Close'].iloc[-1] - df['Close'].iloc[-2]
                    if price_change > 0:
                        return 'BUY', 0.6
                    else:
                        return 'SELL', 0.6
                return 'NEUTRAL', 0.5
            else:
                return 'NEUTRAL', 0.4
        except Exception as e:
            logger.error(f"Volume analysis error: {e}")
            return 'NEUTRAL', 0.5
    
    def _generate_recommendation(self, scores: Dict) -> Tuple[str, float]:
        """
        Generate overall recommendation from all scores.
        
        Returns:
            Tuple of (recommendation, confidence)
        """
        if not scores:
            return 'HOLD', 0.0
        
        # Calculate weighted average
        buy_scores = []
        sell_scores = []
        
        for signal, score in scores.items():
            if signal == 'BUY':
                buy_scores.append(score)
            elif signal == 'SELL':
                sell_scores.append(score)
        
        avg_buy = np.mean(buy_scores) if buy_scores else 0
        avg_sell = np.mean(sell_scores) if sell_scores else 0
        
        if avg_buy > avg_sell and avg_buy > self.min_confidence:
            return 'BUY', avg_buy
        elif avg_sell > avg_buy and avg_sell > self.min_confidence:
            return 'SELL', avg_sell
        else:
            return 'HOLD', max(avg_buy, avg_sell)
    
    def _generate_reason(self, signals: Dict, recommendation: str) -> str:
        """
        Generate human-readable explanation for recommendation.
        """
        reasons = []
        
        for indicator, signal in signals.items():
            if signal == recommendation or (recommendation == 'HOLD' and signal != 'NEUTRAL'):
                reasons.append(f"{indicator}: {signal}")
        
        if reasons:
            return "; ".join(reasons)
        return "Signals mixed or neutral"
    
    def _empty_analysis(self, symbol: str) -> Dict:
        """
        Return empty analysis structure.
        """
        return {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'price': 0,
            'signals': {},
            'scores': {},
            'recommendation': 'HOLD',
            'confidence': 0.0,
            'reason': 'Insufficient data'
        }
    
    def get_signal_explanation(self, analysis: Dict) -> str:
        """
        Get detailed explanation of trading signal.
        
        Args:
            analysis: Analysis dictionary from analyze_stock
            
        Returns:
            Detailed explanation string
        """
        explanation = f"\n{'='*60}\n"
        explanation += f"Symbol: {analysis['symbol']}\n"
        explanation += f"Price: ${analysis['price']:.2f}\n"
        explanation += f"Recommendation: {analysis['recommendation']}\n"
        explanation += f"Confidence: {analysis['confidence']:.2%}\n"
        explanation += f"Reason: {analysis['reason']}\n"
        explanation += f"{'='*60}\n"
        
        return explanation
