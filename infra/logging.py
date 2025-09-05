import logging
import os
from .paths import get_log_directory


def setup_logging() -> logging.Logger:
    log_dir = get_log_directory()
    log_file = os.path.join(log_dir, "app.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("STWv2")


