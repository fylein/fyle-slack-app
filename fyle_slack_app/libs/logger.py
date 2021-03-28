import logging

from django.conf import settings

logging.getLogger('requests').setLevel(logging.ERROR)


class ContextFilter(logging.Filter):
    def filter(self, record):
        record.request_id = '-'
        return True


def get_logger(name):
    """
    log example:
        ERROR 2019-07-03 18:53:35,365 expense_aggregation_service.server: error message
        request_id: 7ca3989edb2a6d9018cfa98d6548a010
    if any other field is interesting, then add to above ContextFilter and %(variable_name)s
    :param name:
    :return:
    """
    logger = logging.getLogger(name)
    logger.level = logging.__dict__[settings.LOG_LEVEL]
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s %(asctime)s %(name)s: %(message)s \nrequest_id:%(request_id)s"))
    handler.addFilter(ContextFilter())
    logger.addHandler(handler)
    return logger
