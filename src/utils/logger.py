"""Unified logging setup for the projection system."""

import logging
import sys
from pathlib import Path
from src.utils.config import Settings


def setup_logger(name: str = "projection_engine", log_file: str | None = None) -> logging.Logger:
    """Configures and returns a logger instance writing to file and stderr.

    Args:
        name: Name of the logger.
        log_file: Target log file path; defaults to Settings.LOG_FILENAME.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(Settings.LOG_FORMAT)

    # File handler (logs warnings, errors, and audit info to project.log)
    target_log = log_file or Settings.LOG_FILENAME
    try:
        file_handler = logging.FileHandler(target_log, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as err:
        sys.stderr.write(f"Warning: Failed to initialize file logger at {target_log}: {err}\n")

    # Console handler for operational warnings and above
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
