import mock

from fyle_slack_app.models import User, Team
from fyle_slack_app.fyle.report_approvals.tasks import process_report_approval


@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.utils')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.WebClient')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.FyleReportApproval')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.slack_utils')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.fyle_utils')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.notification_messages')
def test_report_approve(notification_messages, fyle_utils, slack_utils, fyle_report_approval, slack_client, utils, mock_fyle):
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

    notification_messages.get_report_approval_notification.return_value = 'mock-report-approval-notification-message'

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

    notification_messages.get_report_approval_notification.assert_called()
    notification_messages.get_report_approval_notification.assert_called_with(mock_approved_report['data'], mock_user_display_name, mock_report_url, report_approved_message)
