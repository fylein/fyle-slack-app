from typing import Any, Callable

import hashlib
import hmac
import time

from functools import wraps

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.core.exceptions import ImproperlyConfigured
from django.views import View
from django.utils.decorators import method_decorator

from fyle_slack_app.libs import assertions


def verify_slack_signature(request: HttpRequest) -> bool:
    '''
        Slack creates a unique string for our app and shares it with us.
        This verifies requests from Slack with confidence by verifying signatures using your signing secret.

        On each HTTP request that Slack sends, slack add an X-Slack-Signature HTTP header.
        The signature is created by combining the signing secret with the body of the request slack sends.

        The signature sent by slack in request is checked against the signature we build from the request body.
        Reference: https://api.slack.com/authentication/verifying-requests-from-slack#verifying-requests-from-slack-using-signing-secrets__app-management-updates
    '''
    slack_signature = request.META.get('HTTP_X_SLACK_SIGNATURE')
    slack_request_timestamp = request.META.get('HTTP_X_SLACK_REQUEST_TIMESTAMP')

    is_signature_verified = True

    if not slack_signature or not slack_request_timestamp:
        is_signature_verified = False

    if slack_request_timestamp is not None and time.time() - int(slack_request_timestamp) > 60 * 5:
        # The request timestamp is more than five minutes from local time.
        # It could be a replay attack, so let's ignore it.
        is_signature_verified = False

    if is_signature_verified:
        request_body = request.body.decode("utf-8")

        basestring = "v0:{}:{}".format(slack_request_timestamp, request_body).encode('utf-8')

        try:
            slack_signing_secret = bytes(settings.SLACK_SIGNING_SECRET, 'utf-8')
        except AttributeError as error:
            raise ImproperlyConfigured(
                "`settings.SLACK_SIGNING_SECRET` isn't defined"
            ) from error

        my_signature = 'v0=' + hmac.new(slack_signing_secret, basestring, hashlib.sha256).hexdigest()

        is_signature_verified = hmac.compare_digest(my_signature, slack_signature)

    return is_signature_verified


def verify_slack_request(function: Callable) -> Callable:
    @wraps(function)
    def function_wrapper(request: HttpRequest, *args: Any, **kwargs: Any):
        if not verify_slack_signature(request):
            assertions.assert_true(False, 'Invalid slack request')
        return function(request, *args, **kwargs)
    function_wrapper.csrf_exempt = True
    return function_wrapper


# Base class for all Slack functionalities
class SlackView(View):

    @method_decorator(verify_slack_request)
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)
