"""Enhanced logging configuration for CATT."""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors.

        Args:
            record: Log record

        Returns:
            Formatted string
        """
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{self.BOLD}{levelname}{self.RESET}"
            )

        # Format the message
        result = super().format(record)

        # Reset levelname for other formatters
        record.levelname = levelname

        return result


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    log_dir: Optional[Path] = None,
    console: bool = True,
    colored: bool = True,
) -> None:
    """Setup logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        log_dir: Directory for log files (optional, used if log_file not specified)
        console: Enable console logging
        colored: Use colored console output
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))

        if colored and sys.stdout.isatty():
            console_format = "%(levelname)s %(name)s: %(message)s"
            console_formatter = ColoredFormatter(console_format)
        else:
            console_format = "%(levelname)-8s %(name)s: %(message)s"
            console_formatter = logging.Formatter(console_format)

        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if log_file or log_dir:
        if not log_file and log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "catt.log"

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        file_handler.setLevel(logging.DEBUG)  # Always debug in files

        file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        file_formatter = logging.Formatter(file_format)
        file_handler.setFormatter(file_formatter)

        root_logger.addHandler(file_handler)

    # Set levels for noisy libraries
    logging.getLogger("watchdog").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """Context manager for temporary log level changes."""

    def __init__(self, logger: logging.Logger, level: str):
        """Initialize log context.

        Args:
            logger: Logger to modify
            level: Temporary log level
        """
        self.logger = logger
        self.new_level = getattr(logging, level.upper())
        self.old_level = logger.level

    def __enter__(self) -> logging.Logger:
        """Enter context - change log level."""
        self.logger.setLevel(self.new_level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - restore log level."""
        self.logger.setLevel(self.old_level)


def with_log_level(logger: logging.Logger, level: str) -> LogContext:
    """Create a log context with temporary level.

    Args:
        logger: Logger to modify
        level: Temporary log level

    Returns:
        Log context manager

    Example:
        with with_log_level(logger, "DEBUG"):
            logger.debug("This will be logged")
    """
    return LogContext(logger, level)
