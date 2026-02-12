import logging


def setup_logger():
    logger = logging.getLogger("tatd_project_logger")

    logging.basicConfig(
        handlers=[logging.StreamHandler()],
        level=logging.INFO,
        format="[{asctime}] #{levelname:8} - {name} - {message}",
        style="{"
    )

    return logger


logger = setup_logger()
