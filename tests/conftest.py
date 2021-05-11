import json
import mock
import pytest


@pytest.fixture
def mock_fyle():
    mock_data = open('tests/mock_data.json')
    mock_data = json.load(mock_data)

    fyle = mock.Mock()
    fyle.approver.reports.list.return_value = mock_data['approver']['reports']['list']
    fyle.approver.reports.get.return_value = mock_data['approver']['reports']['get']
    fyle.approver.reports.approve.return_value = mock_data['approver']['reports']['approve']

    return fyle
