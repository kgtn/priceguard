"""
Logging configuration for the PriceGuard bot.
File: src/core/logging.py
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logging(log_dir: str = "logs", log_level: int = logging.INFO) -> None:
    """
    Setup application logging with both file and console handlers.
    
    Args:
        log_dir: Directory to store log files
        log_level: Logging level (default: INFO)
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Create and setup file handler for all logs
    all_logs_handler = RotatingFileHandler(
        log_path / "priceguard.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    all_logs_handler.setFormatter(file_formatter)
    all_logs_handler.setLevel(log_level)
    root_logger.addHandler(all_logs_handler)

    # Create and setup file handler for errors
    error_logs_handler = RotatingFileHandler(
        log_path / "errors.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_logs_handler.setFormatter(file_formatter)
    error_logs_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_logs_handler)

    # Create and setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (default: None, returns root logger)
    
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)
