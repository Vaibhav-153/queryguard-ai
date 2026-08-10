"""Small logging setup shared by API, scripts, and evaluation."""

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure predictable console logs once per process."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
        force=True,
    )
