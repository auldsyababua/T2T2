import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
import os
from typing import Optional

# Create logs directory
LOG_DIR = Path(os.getenv("LOG_FILE", "/Users/colinaulds/.mcp/logs/t2t2_rag.log")).parent
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log format with more detail
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str,
    level: str = None,
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    Set up a logger with both file and console handlers.
    
    Args:
        name: Logger name (usually __name__)
        level: Log level (defaults to LOG_LEVEL env var or INFO)
        log_file: Optional specific log file (defaults to main log file)
        console: Whether to also log to console
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Set level
    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # File handler with rotation
    if log_file is None:
        log_file = os.getenv("LOG_FILE", str(LOG_DIR / "t2t2_rag.log"))
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(file_handler)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(console_handler)
    
    return logger


# Convenience function for request logging
def log_api_request(logger: logging.Logger, method: str, path: str, **kwargs):
    """Log API request details"""
    logger.info(f"API Request: {method} {path}", extra={
        "method": method,
        "path": path,
        **kwargs
    })


def log_api_response(logger: logging.Logger, status_code: int, duration_ms: float, **kwargs):
    """Log API response details"""
    logger.info(f"API Response: {status_code} ({duration_ms:.2f}ms)", extra={
        "status_code": status_code,
        "duration_ms": duration_ms,
        **kwargs
    })


def log_db_query(logger: logging.Logger, query: str, duration_ms: float, **kwargs):
    """Log database query details"""
    logger.debug(f"DB Query ({duration_ms:.2f}ms): {query[:100]}...", extra={
        "query": query,
        "duration_ms": duration_ms,
        **kwargs
    })


def log_telegram_event(logger: logging.Logger, event_type: str, user_id: int, **kwargs):
    """Log Telegram-related events"""
    logger.info(f"Telegram Event: {event_type} for user {user_id}", extra={
        "event_type": event_type,
        "user_id": user_id,
        **kwargs
    })


def log_embedding_operation(logger: logging.Logger, operation: str, count: int, duration_ms: float, **kwargs):
    """Log embedding operations"""
    logger.info(f"Embedding {operation}: {count} items ({duration_ms:.2f}ms)", extra={
        "operation": operation,
        "count": count,
        "duration_ms": duration_ms,
        **kwargs
    })


def log_error_with_context(logger: logging.Logger, error: Exception, context: str, **kwargs):
    """Log errors with additional context"""
    logger.error(f"{context}: {type(error).__name__}: {str(error)}", extra={
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        **kwargs
    }, exc_info=True)