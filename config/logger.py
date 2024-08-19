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
        # Create a base JSON record including level and logger name
        log_record = {
            'level': record.levelname,
            'logger': record.name,
            'message': message
        }
        # Add extra fields from the extra dictionary
        log_record.update(extra)

        return log_record


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
