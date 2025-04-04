import logging
from logging.handlers import RotatingFileHandler

from config.settings import LOG_FILE_PATH


def setup_logger():
    logger = logging.getLogger("tatd_project_logger")

    file_handler = RotatingFileHandler(
        LOG_FILE_PATH, maxBytes=1 * 1024 * 1024, backupCount=2
    )
    console_handler = logging.StreamHandler()

    logging.basicConfig(
        handlers=[file_handler, console_handler],
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    return logger


logger = setup_logger()
