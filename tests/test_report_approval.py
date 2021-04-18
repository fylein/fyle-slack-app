import mock

from fyle_slack_app.models import ReportPollingDetail, User
from fyle_slack_app.fyle.report_approvals.tasks import poll_report_approvals


@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.ReportPollingDetail')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.WebClient')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.FyleReportApproval')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.fyle_utils')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.slack_utils')
@mock.patch('fyle_slack_app.fyle.report_approvals.tasks.report_approval_messages')
def test_report_polling(report_approval_messages, slack_utils, fyle_utils, fyle_report_approval, slack_client, report_polling_detail):
    mock_user = mock.Mock(spec=User)
    mock_user.fyle_user_id = 'mock-fyle-approver-user-id'

    mock_report_polling_detail = mock.Mock(spec=ReportPollingDetail)
    mock_report_polling_detail.slack_user = mock_user

    mock_report_polling_objects = [
        mock_report_polling_detail
    ]
    report_polling_detail.objects.select_related.return_value.all.return_value = mock_report_polling_objects

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

    mock_report_details = {
        'id': 'mock-user-id',
        'org_id': 'orwruogwnngg',
        'created_at': '2020-06-01T13:14:54.804+00:00',
        'updated_at': '2020-06-11T13:14:55.201598+00:00',
        'user_id': 'mock-user-id',
        'user': mock_user_details,
        'purpose': 'Business trip to London',
        'currency': 'INR',
        'amount': 47.99,
        'tax': 18.23,
        'state': 'APPROVER_PENDING',
        'num_expenses': 3,
        'is_manually_flagged': True,
        'is_policy_flagged': True,
        'reimbursed_at': '2020-06-11T13:14:55.201598+00:00',
        'approved_at': '2020-06-11T13:14:55.201598+00:00',
        'submitted_at': '2020-06-11T13:14:55.201598+00:00',
        'claim_number': 'C/2021/02/R/907',
        'source': 'string',
        'approvals': [
            {
                "approver_user_id": "mock-user-id",
                "approver_user": {
                    "id": "mock-user-id",
                    "email": "john.doe@example.com",
                    "full_name": "John Doe"
                },
                "state": "APPROVAL_PENDING"
            }
        ]
    }

    fyle_report_approval.get_approver_reports.return_value = {
        'count': 1,
        'offset': 0,
        'data': [
            mock_report_details
        ]
    }

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
    report_polling_detail.objects.select_related.assert_called_once()
    report_polling_detail.objects.select_related.assert_called_once_with('slack_user__slack_team')
    report_polling_detail.objects.select_related.return_value.all.assert_called_once()

    fyle_report_approval.get_approver_reports.assert_called()
    fyle_report_approval.get_approver_reports.assert_called_with(mock_user, mock_query_params)

    fyle_utils.get_fyle_report_url.assert_called()
    fyle_utils.get_fyle_report_url.assert_called_with(mock_user.fyle_refresh_token)

    slack_utils.get_user_display_name.assert_called()
    slack_utils.get_user_display_name.assert_called_with(slack_client(), mock_user_details)

    report_approval_messages.get_report_approval_notification.assert_called()
    report_approval_messages.get_report_approval_notification.assert_called_with(mock_report_details, mock_user_display_name, mock_report_url)
