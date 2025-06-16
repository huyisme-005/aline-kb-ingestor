"""
backend/utils/logger.py

Configures a standard logger for the ingestor application.
"""

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger("kb_ingestor")
