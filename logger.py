import logging
import sys
from logging.handlers import RotatingFileHandler
from config import LOGS_DIR

def setup_logger():
    logger = logging.getLogger("StoryScheduler")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File Handler (rotating, max 5MB, 5 backups)
        log_file = LOGS_DIR / "app.log"
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5*1024*1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

logger = setup_logger()

# Helper for masking passwords/tokens
def mask_secret(secret_str):
    if not secret_str:
        return ""
    if len(secret_str) <= 4:
        return "*" * len(secret_str)
    return secret_str[:2] + "*" * (len(secret_str) - 4) + secret_str[-2:]
