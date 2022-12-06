import mock
import pytest
from django.http import HttpRequest
from fyle_slack_app.slack import verify_slack_signature

def test_verify_slack_signature(mocker):
    mock_request = mock.MagicMock(spec = HttpRequest)
    mock_request.META = {
        'HTTP_X_SLACK_SIGNATURE': 'HTTP_X_SLACK_SIGNATURE',
        'HTTP_X_SLACK_REQUEST_TIMESTAMP': 2000
    }
    mock_request.body = {
        'data': [1, 2, 3]
    }
    assert not verify_slack_signature(mock_request)