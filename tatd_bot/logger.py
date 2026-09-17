import logging


def setup_logger(log_format: str, env: str) -> logging.Logger:

    logger = logging.getLogger()

    std_out_handler = logging.StreamHandler()
    formatter = logging.Formatter(log_format, style="{")

    if env == "DEV":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    std_out_handler.setFormatter(formatter)
    logger.addHandler(std_out_handler)
    return logger
