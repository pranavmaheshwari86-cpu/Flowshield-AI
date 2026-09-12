"""
ml/src/utils/logger.py
Standardized structured logging for FlowShield ML pipelines.
"""

import logging
import sys


def get_logger(name: str = "flowshield.ml", level: int = logging.INFO) -> logging.Logger:
    """Returns a configured logger instance with formatted console output."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
