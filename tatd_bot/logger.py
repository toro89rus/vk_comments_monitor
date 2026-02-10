import logging


def setup_logger():
    logger = logging.getLogger("tatd_project_logger")

    logging.basicConfig(
        handlers=[logging.StreamHandler()],
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    return logger


logger = setup_logger()
