from typing import Dict

import os
import json
import mock
import pytest
import requests

from fyle.platform import Platform
from django.conf import settings
from fyle_slack_app.models import User

FYLE_STOPLIGHT_URL = os.environ.get('FYLE_STOPLIGHT_URL')


def http_request(method: str, url: str) -> Dict:
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request(method=method, headers=headers, url=url)

    return response.json()


@pytest.fixture
def mock_fyle() -> Platform:

    fyle = mock.Mock()

    # Approver API mocks
    approver_reports_list_response = http_request(
        method='GET',
        url='{}/4617647/approver/reports'.format(FYLE_STOPLIGHT_URL)
    )

    # Subscriptions API adds this extra key which is not present in resource API response
    approver_reports_list_response['data'][0]['updated_by_user'] = {
        'id': 'mock-user-id-2',
        'full_name': 'John Doe',
        'email': 'john.doe@example.com'
    }

    approver_reports_get_response = {
        'data': approver_reports_list_response['data'][0]
    }

    fyle.approver.reports.list.return_value = approver_reports_list_response

    fyle.approver.reports.get.return_value = approver_reports_get_response

    fyle.approver.reports.approve.return_value = approver_reports_get_response

    # Fyler API mocks
    fyle.spender.my_profile.get.return_value = http_request(
        method='GET',
        url='{}/28670828/spender/my_profile'.format(FYLE_STOPLIGHT_URL)
    )

    return fyle

@pytest.fixture()
def test_connection(db):
    """
    Creates a connection with Fyle
    """
    client_id = settings.FYLE_CLIENT_ID
    client_secret = settings.FYLE_CLIENT_SECRET
    token_url = settings.FYLE_TOKEN_URI
    refresh_token = settings.FYLE_REFRESH_TOKEN
    server_url = settings.FYLE_SERVER_URL
    fyle_connection = Platform(
        token_url=token_url,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        server_url=server_url
    )

    return fyle_connection

@pytest.fixture()
def report_approval_user(request, mocker, test_connection):
    mocker_1 = mocker.patch('fyle_slack_app.fyle.utils.get_fyle_sdk_connection', return_value = test_connection)
    user = mock.Mock(spec = User)
    user.fyle_refresh_token = 'dummy-refresh-token'
    return user
