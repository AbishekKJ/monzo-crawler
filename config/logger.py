import os
import logging
import json_log_formatter
from typing import Dict, Any


class JSONFormatter(json_log_formatter.JSONFormatter):
    def json_record(self, message: str, extra: Dict[str, Any], record: logging.LogRecord) -> Dict[str, Any]:
        """
        Customize the JSON log record format.

        Args:
            message (str): The log message.
            extra (Dict[str, Any]): Extra context provided to the logger.
            record (logging.LogRecord): The log record.

        Returns:
            Dict[str, Any]: The JSON-structured log record.
        """
        extra['level'] = record.levelname
        extra['logger'] = record.name
        return extra


def configure_logger(logging_config: Dict[str, str]) -> None:
    """
    Configure the logger based on the provided settings.

    Args:
        logging_config (Dict[str, str]): A dictionary with logging settings, e.g., {'level': 'INFO'}.
    """
    formatter = JSONFormatter()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging_config.get('level', 'INFO'))
    logger.addHandler(handler)


def setup_logging() -> None:
    """
    Set up logging based on environment using JSONFormatter.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging_config = {
        'level': log_level
    }
    configure_logger(logging_config)
