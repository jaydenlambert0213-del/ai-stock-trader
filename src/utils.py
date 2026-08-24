"""Utility functions for logging and helpers."""

import logging
import os
from datetime import datetime


def setup_logging(log_file: str = 'logs/trading.log', level=logging.INFO):
    """
    Setup logging configuration.
    
    Args:
        log_file: Path to log file
        level: Logging level
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def format_currency(value: float) -> str:
    """
    Format value as currency string.
    
    Args:
        value: Numerical value
        
    Returns:
        Formatted currency string
    """
    return f"${value:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format value as percentage string.
    
    Args:
        value: Numerical value
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimals}f}%"


def get_market_open_time():
    """
    Get market open time for US markets (9:30 AM EST).
    
    Returns:
        Datetime object for market open
    """
    now = datetime.now()
    return now.replace(hour=9, minute=30, second=0, microsecond=0)


def get_market_close_time():
    """
    Get market close time for US markets (4:00 PM EST).
    
    Returns:
        Datetime object for market close
    """
    now = datetime.now()
    return now.replace(hour=16, minute=0, second=0, microsecond=0)
