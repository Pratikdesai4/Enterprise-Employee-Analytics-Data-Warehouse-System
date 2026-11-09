"""
Enterprise Employee Analytics - Centralized Logging Configuration
=================================================================
Provides structured application-wide logging with configurable log levels
and consistent formatting across modules.

Author: Enterprise Data Architecture Team
"""

import os
import sys
import logging
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Retrieves or configures a standardized application logger."""
    logger_name = f"enterprise_analytics.{name}" if name else "enterprise_analytics"
    logger = logging.getLogger(logger_name)

    if not logger.handlers:
        level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_str, logging.INFO)
        logger.setLevel(level)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
