import logging
from tatd_bot.config.settings import ENV


def setup_logger(env: str):
    logger = logging.getLogger("tatd_project_logger")

    std_oud_hadnler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[{asctime}] #{levelname:8} - {name} - {message}", style="{"
    )

    if env == "dev":
        std_oud_hadnler.setLevel(logging.DEBUG)
    else:
        std_oud_hadnler.setLevel(logging.INFO)

    std_oud_hadnler.setFormatter(formatter)
    logger.addHandler(std_oud_hadnler)

    return logger


logger = setup_logger(ENV)
