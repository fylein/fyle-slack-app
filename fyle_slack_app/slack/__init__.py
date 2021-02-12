import hashlib
import hmac
import time

from functools import wraps
from typing import Any

from django import http
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.views import View
from django.utils.decorators import method_decorator

from fyle_slack_app.libs import assertions


def verify_slack_signature(request) -> bool:
    slack_signature = request.META.get('HTTP_X_SLACK_SIGNATURE')
    slack_request_timestamp = request.META.get('HTTP_X_SLACK_REQUEST_TIMESTAMP')

    if not slack_signature or not slack_request_timestamp:
        return False

    if time.time() - int(slack_request_timestamp) > 60 * 5:
        # The request timestamp is more than five minutes from local time.
        # It could be a replay attack, so let's ignore it.
        return False

    request_body = request.body.decode("utf-8")

    basestring = "v0:{}:{}".format(slack_request_timestamp, request_body).encode('utf-8')

    try:
        slack_signing_secret = bytes(settings.SLACK_SIGNING_SECRET, 'utf-8')
    except AttributeError:
        raise ImproperlyConfigured(
            "`settings.SLACK_SIGNING_SECRET` isn't defined"
        )

    my_signature = 'v0=' + hmac.new(slack_signing_secret, basestring, hashlib.sha256).hexdigest()

    return hmac.compare_digest(my_signature, slack_signature)


def verify_slack_request(function):
    @wraps(function)
    def function_wrapper(request, *args, **kwargs):
        if not verify_slack_signature(request):
            assertions.assert_true(False, 'Invalid slack request')
        return function(request, *args, **kwargs)
    function_wrapper.csrf_exempt = True
    return function_wrapper

class SlackView(View):
    @method_decorator(verify_slack_request)
    def dispatch(self, request: http.HttpRequest, *args: Any, **kwargs: Any) -> http.HttpResponse:
        return super(SlackView, self).dispatch(request, *args, **kwargs)