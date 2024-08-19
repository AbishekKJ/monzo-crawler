import logging
import json_log_formatter


class JSONFormatter(json_log_formatter.JSONFormatter):
    def json_record(self, message, extra, record):
        extra['level'] = record.levelname
        extra['logger'] = record.name
        return extra


def configure_logger(logging_config):
    formatter = JSONFormatter()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging_config['level'])
    logger.addHandler(handler)
