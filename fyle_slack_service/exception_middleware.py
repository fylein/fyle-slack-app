import traceback

from django.http import JsonResponse
from django.db import IntegrityError
from django.utils.deprecation import MiddlewareMixin

from fyle_slack_app.libs.assertions import InvalidUsage
from fyle_slack_app.libs.logger import get_logger


logger = get_logger(__name__)

class CustomExceptionMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if isinstance(exception, InvalidUsage):
            resp = exception.to_dict()
            status = exception.status_code
        if isinstance(exception, IntegrityError):
            resp = {
                'message': 'Seems like an error occured on our side'
            }
            status = 400
        else:
            code = 500
            resp = {
                'message': str(exception)
            }
            status = code
            logger.error(traceback.format_exc())

        return JsonResponse(resp, status=status)
