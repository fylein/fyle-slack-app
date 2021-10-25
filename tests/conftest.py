from typing import Dict

import os
import json
import mock
import pytest
import requests

from fyle.platform import Platform


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
    fyle.fyler.my_profile.get.return_value = http_request(
        method='GET',
        url='{}/4617658/fyler/my_profile'.format(FYLE_STOPLIGHT_URL)
    )

    return fyle
