import logging
from logging.handlers import RotatingFileHandler
from prometheus_client import Counter

logger_errors = Counter("app_errors_total", "Total errors logged")

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler("app.log", maxBytes = 10_000_000, backupCount = 5)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    logger.error = lambda msg, *args: [logger_errors.inc(), logger.error(msg, *args)][1]
    return logger