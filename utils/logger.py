"""
Structured logging configuration for the Egypt Phone Prices scraping pipeline.

This module provides a centralized logging setup with support for:
- Console and file logging
- Structured JSON output for production environments
- Different log levels for development and production
- Pipeline-specific context tracking
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from functools import wraps


# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs.
    Useful for production environments and log aggregation services.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "pipeline_context"):
            log_data["context"] = record.pipeline_context
        
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class StandardFormatter(logging.Formatter):
    """
    Custom formatter for readable console output.
    """

    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        level = record.levelname
        color = self.COLORS.get(level, "")
        record.levelname = f"{color}{level}{self.RESET}"

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        # Build log message
        log_message = f"[{timestamp}] {record.levelname} - {record.name} - {record.getMessage()}"

        # Add context if present
        if hasattr(record, "pipeline_context"):
            log_message += f" | Context: {record.pipeline_context}"

        # Add exception info
        if record.exc_info:
            log_message += f"\n{self.formatException(record.exc_info)}"

        return log_message


def get_logger(
    name: str,
    log_level: Optional[str] = None,
    use_json: bool = False,
    use_file: bool = True,
) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  Defaults to INFO
        use_json: Whether to use JSON formatting (for production)
        use_file: Whether to log to file in addition to console

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if logger.handlers:
        return logger

    # Set log level
    level = getattr(logging, log_level or "INFO")
    logger.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if use_json:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(StandardFormatter())

    logger.addHandler(console_handler)

    # File handler (if enabled)
    if use_file:
        log_file = LOGS_DIR / f"{name.replace('.', '_')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(
            StructuredFormatter() if use_json else StandardFormatter()
        )
        logger.addHandler(file_handler)

    return logger


def log_with_context(context: Dict[str, Any]):
    """
    Decorator to add context information to log messages.

    Args:
        context: Dictionary containing context information
                (e.g., source, item_id, scrape_session_id)

    Example:
        @log_with_context({"source": "amazon", "item_id": "12345"})
        def scrape_item(item_id):
            logger.info("Scraping item")  # Will include context
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Store context in thread-local storage or pass via logger
            logger = logging.getLogger(func.__module__)
            
            # Create a custom log record factory to include context
            original_factory = logging.getLogRecordFactory()
            
            def context_log_factory(*args, **kwargs):
                record = original_factory(*args, **kwargs)
                record.pipeline_context = context
                return record
            
            logging.setLogRecordFactory(context_log_factory)
            
            try:
                return func(*args, **kwargs)
            finally:
                logging.setLogRecordFactory(original_factory)
        
        return wrapper
    return decorator


class PipelineLogger:
    """
    Specialized logger for the scraping pipeline with built-in context tracking.
    """

    def __init__(
        self,
        name: str,
        log_level: str = "INFO",
        use_json: bool = False,
    ):
        self.logger = get_logger(name, log_level, use_json)
        self.context: Dict[str, Any] = {}

    def set_context(self, **kwargs):
        """Set pipeline context (e.g., source, session_id)."""
        self.context.update(kwargs)

    def clear_context(self):
        """Clear pipeline context."""
        self.context.clear()

    def debug(self, message: str, extra_data: Optional[Dict] = None):
        """Log debug message with optional extra data."""
        self._log(logging.DEBUG, message, extra_data)

    def info(self, message: str, extra_data: Optional[Dict] = None):
        """Log info message with optional extra data."""
        self._log(logging.INFO, message, extra_data)

    def warning(self, message: str, extra_data: Optional[Dict] = None):
        """Log warning message with optional extra data."""
        self._log(logging.WARNING, message, extra_data)

    def error(self, message: str, extra_data: Optional[Dict] = None):
        """Log error message with optional extra data."""
        self._log(logging.ERROR, message, extra_data)

    def critical(self, message: str, extra_data: Optional[Dict] = None):
        """Log critical message with optional extra data."""
        self._log(logging.CRITICAL, message, extra_data)

    def _log(self, level: int, message: str, extra_data: Optional[Dict] = None):
        """Internal logging method with context support."""
        extra = {"pipeline_context": self.context}
        if extra_data:
            extra["extra_data"] = extra_data
        
        self.logger.log(level, message, extra=extra)

    def log_scrape_start(self, source: str, url: str):
        """Log the start of a scraping operation."""
        self.set_context(source=source, url=url)
        self.info(
            f"Starting scrape from {source}",
            extra_data={"url": url}
        )

    def log_scrape_end(self, source: str, items_scraped: int, duration_seconds: float):
        """Log the end of a scraping operation."""
        self.info(
            f"Completed scrape from {source}",
            extra_data={
                "items_scraped": items_scraped,
                "duration_seconds": duration_seconds
            }
        )

    def log_item_scraped(self, item_id: str, item_data: Dict[str, Any]):
        """Log a successfully scraped item."""
        self.info(
            f"Item scraped: {item_id}",
            extra_data={"item": item_data}
        )

    def log_scrape_error(self, source: str, error: Exception, url: Optional[str] = None):
        """Log a scraping error."""
        self.error(
            f"Error scraping from {source}: {str(error)}",
            extra_data={
                "error_type": type(error).__name__,
                "url": url
            }
        )


# Default pipeline logger instance
pipeline_logger = PipelineLogger("egypt_phone_prices.pipeline")
