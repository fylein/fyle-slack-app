import json
import uuid
import mock
import pytest

from django.http import JsonResponse

from slack_sdk.web import WebClient

from fyle_slack_app.models import NotificationPreference, User, UserSubscriptionDetail
from fyle_slack_app.models.notification_preferences import NotificationType
from fyle_slack_app.fyle.notifications.views import FyleFylerNotification, FyleApproverNotification, FyleNotificationView
from fyle_slack_app.fyle.notifications.views import FyleNotificationView

# This is needed to parameterize the tests
FYLER_NOTIFICATION_TYPES = [
    NotificationType.REPORT_COMMENTED,
    NotificationType.REPORT_PARTIALLY_APPROVED,
    NotificationType.REPORT_SUBMITTED,
    NotificationType.REPORT_PAYMENT_PROCESSING,
    NotificationType.REPORT_APPROVER_SENDBACK
]

APPROVER_NOTIFICATION_TYPES = [
    NotificationType.REPORT_SUBMITTED
]


@mock.patch('fyle_slack_app.fyle.notifications.views.utils')
@mock.patch('fyle_slack_app.fyle.notifications.views.NotificationPreference')
@mock.patch('fyle_slack_app.fyle.notifications.views.User')
@mock.patch('fyle_slack_app.fyle.notifications.views.slack_utils')
@mock.patch('fyle_slack_app.fyle.notifications.views.fyle_utils')
@mock.patch.object(FyleNotificationView, 'track_notification')
@pytest.mark.parametrize('notification_type', [notification_type for (notification_type) in FYLER_NOTIFICATION_TYPES])
def test_fyler_notifications(track_notification, fyle_utils, slack_utils, user, notification_preference, utils, notification_type, mock_fyle):

    mock_webhook_id = str(uuid.uuid4())

    mock_slack_user_id = 'mock-slack-user-id'
    mock_slack_team_id = 'mock-slack-team-id'
    mock_fyle_refresh_token = 'mock-fyle-refresh-token'

    mock_report = mock_fyle.approver.reports.get()

    notification_type_split = notification_type.value.split('_')

    resource = notification_type_split[0]
    action = '_'.join(notification_type_split[1:])

    mock_webhook_data = {
        'resource': resource,
        'action': action,
        'data': mock_report['data'],
        'reason': 'mock-reason'
    }

    mock_request = mock.Mock()

    mock_request.body = json.dumps(mock_webhook_data)

    mock_user_subscription_detail = mock.Mock(spec=UserSubscriptionDetail)


    mock_user_subscription_detail.slack_user_id = mock_slack_user_id

    utils.get_or_none.return_value = mock_user_subscription_detail

    mock_notification_preference = mock.Mock(spec=NotificationPreference)
    notification_preference.objects.get.return_value = mock_notification_preference
    mock_notification_preference.is_enabled = True

    mock_user = mock.Mock(spec=User)

    user.objects.get.return_value = mock_user
    mock_user.slack_team_id = mock_slack_team_id
    mock_user.fyle_refresh_token = mock_fyle_refresh_token

    mock_slack_client = mock.Mock(spec=WebClient)
    slack_utils.get_slack_client.return_value = mock_slack_client

    mock_slack_client.chat_postMessage.return_value = None

    mock_fyle_report_url = 'mock-fyle-report-url'
    fyle_utils.get_fyle_resource_url.return_value = mock_fyle_report_url

    track_notification.return_value = None

    # Calling the function to be test
    response = FyleFylerNotification().post(mock_request, mock_webhook_id)

    # Checking response type
    assert isinstance(response, JsonResponse)

    # Checking the required methods have been called
    utils.get_or_none.assert_called()
    utils.get_or_none.assert_called_with(UserSubscriptionDetail, webhook_id=mock_webhook_id)

    notification_preference.objects.get.assert_called()
    notification_preference.objects.get.assert_called_with(slack_user_id=mock_slack_user_id, notification_type=notification_type.value)

    user.objects.get.assert_called()
    user.objects.get.assert_called_with(slack_user_id=mock_slack_user_id)

    mock_slack_client.chat_postMessage.assert_called()

    track_notification.assert_called()



@mock.patch('fyle_slack_app.fyle.notifications.views.utils')
@mock.patch('fyle_slack_app.fyle.notifications.views.NotificationPreference')
@mock.patch('fyle_slack_app.fyle.notifications.views.User')
@mock.patch('fyle_slack_app.fyle.notifications.views.slack_utils')
@mock.patch('fyle_slack_app.fyle.notifications.views.fyle_utils')
@mock.patch.object(FyleNotificationView, 'track_notification')
@pytest.mark.parametrize('notification_type', [notification_type for (notification_type) in APPROVER_NOTIFICATION_TYPES])
def test_approver_notifications(track_notification, fyle_utils, slack_utils, user, notification_preference, utils, notification_type, mock_fyle):

    mock_webhook_id = str(uuid.uuid4())

    mock_slack_user_id = 'mock-slack-user-id'
    mock_slack_team_id = 'mock-slack-team-id'
    mock_fyle_refresh_token = 'mock-fyle-refresh-token'

    mock_report = mock_fyle.approver.reports.get()

    notification_type_split = notification_type.value.split('_')

    resource = notification_type_split[0]
    action = '_'.join(notification_type_split[1:])

    mock_report['data']['state'] = 'APPROVER_PENDING'

    mock_webhook_data = {
        'resource': resource,
        'action': action,
        'data': mock_report['data']
    }

    mock_request = mock.Mock()

    mock_request.body = json.dumps(mock_webhook_data)

    mock_user_subscription_detail = mock.Mock(spec=UserSubscriptionDetail)


    mock_user_subscription_detail.slack_user_id = mock_slack_user_id

    utils.get_or_none.return_value = mock_user_subscription_detail

    mock_notification_preference = mock.Mock(spec=NotificationPreference)
    notification_preference.objects.get.return_value = mock_notification_preference
    mock_notification_preference.is_enabled = True

    mock_user = mock.Mock(spec=User)

    user.objects.get.return_value = mock_user
    mock_user.slack_team_id = mock_slack_team_id
    mock_user.fyle_refresh_token = mock_fyle_refresh_token

    mock_slack_client = mock.Mock(spec=WebClient)
    slack_utils.get_slack_client.return_value = mock_slack_client

    mock_slack_client.chat_postMessage.return_value = None

    mock_fyle_report_url = 'mock-fyle-report-url'
    fyle_utils.get_fyle_resource_url.return_value = mock_fyle_report_url

    track_notification.return_value = None

    # Calling the function to be test
    response = FyleApproverNotification().post(mock_request, mock_webhook_id)

    # Checking response type
    assert isinstance(response, JsonResponse)

    # Checking the required methods have been called
    utils.get_or_none.assert_called()
    utils.get_or_none.assert_called_with(UserSubscriptionDetail, webhook_id=mock_webhook_id)

    notification_preference.objects.get.assert_called()
    notification_preference.objects.get.assert_called_with(slack_user_id=mock_slack_user_id, notification_type=notification_type.value)

    user.objects.get.assert_called()
    user.objects.get.assert_called_with(slack_user_id=mock_slack_user_id)

    mock_slack_client.chat_postMessage.assert_called()

    track_notification.assert_called()


class TestNotifications:
    def test_get_report_tracking_data(self):
        mock_user = mock.MagicMock(spec = User)
        mock_user.slack_user_id = 'slack_user_id'
        mock_user.fyle_user_id = 'fyle_user_id'
        mock_user.email = 'email@gmail.com'
        mock_user.slack_team.id = 'slack_team_id'
        mock_user.slack_team.name = 'slack_team_name'
        report_data = {
            'id': 'id', 
            'org_id':'org_id'
        }
        rhs = {
            'asset': 'SLACK_APP',
            'slack_user_id': 'slack_user_id',
            'fyle_user_id': 'fyle_user_id',
            'email': 'email@gmail.com',
            'slack_team_id': 'slack_team_id',
            'slack_team_name': 'slack_team_name',
            'report_id': report_data['id'] , 
            'org_id': report_data['org_id']
        }
        event_data = FyleNotificationView.get_report_tracking_data(mock_user, report_data)
        assert all((rhs.get(key) == value for key, value in event_data.items()))


    def test_track_notification(self, mocker):
        resource_type = 'EXPENSE'
        mock_user = mock.MagicMock(spec = User)
        mock_user.slack_user_id = 'slack_user_id'
        mock_user.fyle_user_id = 'fyle_user_id'
        mock_user.email = 'email@gmail.com'
        mock_user.slack_team.id = 'slack_team_id'
        mock_user.slack_team.name = 'slack_team_name'

        resource = {
            'id': 'id',
            'org_id' : 'org_id' 
        }
        rhs = {
            'asset': 'SLACK_APP',
            'slack_user_id': 'slack_user_id',
            'fyle_user_id': 'fyle_user_id',
            'email': 'email@gmail.com',
            'slack_team_id': 'slack_team_id',
            'slack_team_name': 'slack_team_name',
            'expense_id': resource['id'] , 
            'org_id': resource['org_id']
        }
        event_data = FyleNotificationView.track_notification('event_name', mock_user, resource_type, resource)
        assert all((rhs.get(key) == value for key, value in event_data.items()))
    