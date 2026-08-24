"""AI Stock Trader - Automated trading system with AI-driven decision making."""

__version__ = "1.0.0"
__author__ = "AI Stock Trader Team"

from .indicators import TechnicalIndicators
from .ai_engine import AIEngine
from .portfolio import Portfolio
from .risk_manager import RiskManager
from .market_data import MarketData
from .simulator import TradeSimulator

__all__ = [
    'TechnicalIndicators',
    'AIEngine',
    'Portfolio',
    'RiskManager',
    'MarketData',
    'TradeSimulator',
]
