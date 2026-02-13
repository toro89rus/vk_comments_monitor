import logging
from tatd_bot.config.settings import ENV


def setup_logger(env: str) -> logging.Logger:

    logger = logging.getLogger()

    std_oud_hadnler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[{asctime}] #{levelname:8} - {name} - {message}", style="{"
    )

    if ENV == "dev":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    std_oud_hadnler.setFormatter(formatter)
    logger.addHandler(std_oud_hadnler)
    return logger


logger = setup_logger(ENV)
