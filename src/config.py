"""Configuration utilities for loading and validating config."""

import yaml
import os
from typing import Dict
import logging

logger = logging.getLogger(__name__)


def load_config(config_path: str = 'config/config.yaml') -> Dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file: {e}")
        raise


def validate_config(config: Dict) -> bool:
    """
    Validate configuration dictionary.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if valid, raises exception otherwise
    """
    required_keys = ['trading', 'indicators', 'ai_engine', 'risk_management']
    
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration section: {key}")
    
    # Validate trading config
    trading = config['trading']
    if 'initial_capital' not in trading:
        raise ValueError("Missing 'initial_capital' in trading config")
    if 'symbols' not in trading or not trading['symbols']:
        raise ValueError("Missing or empty 'symbols' in trading config")
    
    # Validate risk management
    risk = config['risk_management']
    if 'max_positions' not in risk:
        raise ValueError("Missing 'max_positions' in risk_management config")
    
    logger.info("Configuration validation passed")
    return True


def get_config_value(config: Dict, path: str, default=None):
    """
    Get value from nested configuration dictionary using dot notation.
    
    Args:
        config: Configuration dictionary
        path: Dot-separated path (e.g., 'trading.initial_capital')
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    keys = path.split('.')
    value = config
    
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
    
    return value if value is not None else default
