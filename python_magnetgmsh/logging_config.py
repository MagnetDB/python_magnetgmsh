"""
Logging configuration for python_magnetgmsh.

Provides centralized logging setup with consistent formatting and
configurable output levels.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    verbose: bool = False,
    debug: bool = False
) -> logging.Logger:
    """
    Configure logging for python_magnetgmsh.
    
    Args:
        level: Base logging level (default: INFO)
        log_file: Optional file path for log output
        verbose: If True, set level to DEBUG
        debug: If True, set level to DEBUG and add more detail
        
    Returns:
        Configured root logger for python_magnetgmsh
        
    Example:
        >>> from python_magnetgmsh.logging_config import setup_logging
        >>> logger = setup_logging(verbose=True)
        >>> logger.info("Processing started")
    """
    # Determine logging level
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    
    # Create logger
    logger = logging.getLogger('python_magnetgmsh')
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    if debug:
        # Detailed format for debug mode
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Simple format for normal operation
        formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)  # Always DEBUG for files
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Module name (use __name__)
        
    Returns:
        Logger instance
        
    Example:
        >>> from python_magnetgmsh.logging_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing geometry")
    """
    return logging.getLogger(f'python_magnetgmsh.{name}')
