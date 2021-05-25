import mock

from fyle_slack_app.models import ReportPollingDetail, User, Team, NotificationPreference
from fyle_slack_app.models.notification_preferences import NotificationType
from fyle_slack_app.fyle.report_approvals.tasks import poll_report_approvals, process_report_approval


@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.ReportPollingDetail')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.WebClient')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.FyleReportApproval')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.fyle_utils')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.slack_utils')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.report_approval_messages')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.NotificationPreference')
def test_report_polling(notification_preference, report_approval_messages, slack_utils, fyle_utils, fyle_report_approval, slack_client, report_polling_detail, mock_fyle):

    mock_user = mock.Mock(spec=User)
    mock_user.fyle_user_id = 'mock-fyle-approver-user-id'

    mock_notification_preference = mock.Mock(spec=NotificationPreference)
    mock_notification_preference.slack_user = mock_user
    notification_preference.objects.select_related.return_value.filter.return_value = [
        mock_notification_preference
    ]

    mock_report_polling_detail = mock.Mock(spec=ReportPollingDetail)

    report_polling_detail.objects.select_related.return_value.get.return_value = mock_report_polling_detail
    report_polling_detail.slack_user = mock_user

    mock_fyle_profile = mock_fyle.fyler.my_profile.get()['data']
    # Adding APPROVER role for testing
    mock_fyle_profile['roles'].append('APPROVER')
    fyle_utils.get_fyle_profile.return_value = mock_fyle_profile

    mock_user_details = {
        'id': 'mock-user-id',
        'email': 'john.doe@example.com',
        'full_name': 'John Doe'
    }

    last_submitted_at = mock_report_polling_detail.last_successful_poll_at.isoformat()

    mock_query_params = {
        'state': 'eq.APPROVER_PENDING',
        'approvals': 'cs.[{{ "approver_user_id": {}, "state": "APPROVAL_PENDING" }}]'.format(mock_report_polling_detail.slack_user.fyle_user_id),
        'last_submitted_at': 'gte.{}'.format(last_submitted_at),

        # Mandatory query params required by sdk
        'limit': 50, # Assuming no more than 50 reports will be there in 10 min poll
        'offset': 0,
        'order': 'last_submitted_at.desc'
    }

    mock_approver_reports = mock_fyle.approver.reports.list()

    fyle_report_approval.get_approver_reports.return_value = mock_approver_reports

    mock_report_url = 'mock-report-url'
    fyle_utils.get_fyle_report_url.return_value = mock_report_url

    mock_user_display_name = 'mock-employee-display-name'
    slack_utils.get_user_display_name.return_value = mock_user_display_name

    mock_report_approval_notification = 'mock-report-approval-notification-message'
    report_approval_messages.get_report_approval_notification.return_value = mock_report_approval_notification

    mock_chat_post_message = 'chat-post-message'
    slack_client.chat_postMessage.return_value = mock_chat_post_message

    # Calling the polling function to be tested
    poll_report_approvals()

    # Assertion check for required methods that have been called
    notification_preference.objects.select_related.assert_called_once()
    notification_preference.objects.select_related.assert_called_once_with('slack_user')
    notification_preference.objects.select_related.return_value.filter.asser_called()
    notification_preference.objects.select_related.return_value.filter.asser_called_with(NotificationType.APPROVER_REPORT_APPROVAL.value, True)

    report_polling_detail.objects.select_related.assert_called()
    report_polling_detail.objects.select_related.assert_called_with('slack_user__slack_team')
    report_polling_detail.objects.select_related.return_value.get.assert_called()

    fyle_utils.get_fyle_profile.assert_called()
    fyle_utils.get_fyle_profile.assert_called_with(mock_user.fyle_refresh_token)

    fyle_report_approval.get_approver_reports.assert_called()
    fyle_report_approval.get_approver_reports.assert_called_with(mock_report_polling_detail.slack_user, mock_query_params)

    fyle_utils.get_fyle_report_url.assert_called()
    fyle_utils.get_fyle_report_url.assert_called_with(mock_report_polling_detail.slack_user.fyle_refresh_token)

    slack_utils.get_user_display_name.assert_called()
    slack_utils.get_user_display_name.assert_called_with(slack_client(), mock_user_details)

    report_approval_messages.get_report_approval_notification.assert_called()
    report_approval_messages.get_report_approval_notification.assert_called_with(mock_approver_reports['data'][0], mock_user_display_name, mock_report_url)


@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.utils')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.WebClient')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.FyleReportApproval')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.slack_utils')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.fyle_utils')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.report_approval_messages')
def test_report_approve(report_approval_messages, fyle_utils, slack_utils, fyle_report_approval, slack_client, utils, mock_fyle):
    mock_team = mock.Mock(spec=Team)
    mock_user = mock.Mock(spec=User)

    mock_fyle_user_id = 'mock-user-id'
    mock_fyle_refresh_token = 'mock-fyle-refresh-token'
    mock_user.fyle_user_id = mock_fyle_user_id
    mock_user.fyle_refresh_token = mock_fyle_refresh_token

    utils.get_or_none.side_effect = [mock_team, mock_user]

    mock_approver_report = mock_fyle.approver.reports.get()

    fyle_report_approval.get_report_by_id.return_value = mock_approver_report

    mock_user_display_name = 'mock-employee-display-name'
    slack_utils.get_user_display_name.return_value = mock_user_display_name

    mock_report_url = 'mock-report-url'
    fyle_utils.get_fyle_report_url.return_value = mock_report_url

    mock_report_message = 'mock-report-message'
    fyle_report_approval.can_approve_report.return_value = (True, mock_report_message)

    mock_approved_report = mock_fyle.approver.reports.approve()
    fyle_report_approval.approve_report.return_value = mock_approved_report

    report_approval_messages.report_approval_messages.return_value = 'mock-report-approval-notification-message'

    mock_chat_post_message = 'chat-post-message'
    slack_client.chat_postMessage.return_value = mock_chat_post_message


    # Calling the function to be tested
    mock_report_id = 'mock-report-id'
    mock_team_id = 'mock-team-id'
    mock_message_timestamp = 'mock-message-timestamp'
    mock_notification_message = 'mock-notification-message'
    report_approved_message = 'Expense report approved :rocket:'

    process_report_approval(mock_report_id, mock_fyle_user_id, mock_team_id, mock_message_timestamp, mock_notification_message)

    # Assertion check for required methods that have been called

    # Check is get_or_none function has been called twice
    assert utils.get_or_none.call_count == 2

    # We call get_or_none twice in view to be tested
    # This check if the parameters passed in each call are correct or not
    expected_calls = [
        mock.call(Team, id=mock_team_id),
        mock.call(User, slack_user_id=mock_fyle_user_id)
    ]

    utils.get_or_none.assert_has_calls(expected_calls)

    fyle_report_approval.get_report_by_id.assert_called()
    fyle_report_approval.get_report_by_id.assert_called_with(mock_user, mock_report_id)

    fyle_report_approval.can_approve_report.assert_called()
    fyle_report_approval.can_approve_report.assert_called_with(mock_approver_report['data'], mock_fyle_user_id)

    slack_utils.get_user_display_name.assert_called()
    slack_utils.get_user_display_name.assert_called_with(slack_client(), mock_approver_report['data']['user'])

    fyle_utils.get_fyle_report_url.assert_called()
    fyle_utils.get_fyle_report_url.assert_called_with(mock_fyle_refresh_token)

    fyle_report_approval.approve_report.assert_called()
    fyle_report_approval.approve_report.assert_called_with(mock_user, mock_report_id)

    report_approval_messages.get_report_approval_notification.assert_called()
    report_approval_messages.get_report_approval_notification.assert_called_with(mock_approved_report['data'], mock_user_display_name, mock_report_url, report_approved_message)
