from django.utils import timezone

from slack_sdk.web import WebClient
from fyle.platform.exceptions import NoPrivilegeError

from ...slack import utils as slack_utils
from ...models import ReportPollingDetail, Team, User
from .views import FyleReportApproval
from .. import utils as fyle_utils
from ...libs import utils, assertions
from ...slack.ui.report_approvals import messages as report_approval_messages


def poll_report_approvals():
    # select_related joins the two table with foriegn key column
    # 1st join -> `report_polling_details` table with `users` table with `user` field
    # 2nd join -> `__slack_team` joins `users` table with `teams` table

    # 2 joins because we need user details (from `users` table) and team details (from `teams` table)
    report_polling_details = ReportPollingDetail.objects.select_related('user__slack_team').all()

    for report_polling_detail in report_polling_details:
        user = report_polling_detail.user

        slack_client = WebClient(token=user.slack_team.bot_access_token)

        approver_id = user.fyle_employee_id

        submitted_at = report_polling_detail.last_successful_poll_at.isoformat()

        # Fetch approver reports to approve - i.e. report state -> APPROVER_PENDING & approval state -> APPROVAL_PENDING
        query_params = {
            'state': 'eq.APPROVER_PENDING',
            'approvals': 'cs.[{{ "approver_id": {}, "state": "APPROVAL_PENDING" }}]'.format(approver_id),
            'submitted_at': 'gte.{}'.format(submitted_at),

            # Mandatory query params required by sdk
            'limit': 10, # Assuming no more than 10 reports will be there in 10 min poll
            'offset': 0,
            'order': 'submitted_at.desc'
        }

        # Since not all users will be approvers so the sdk api call with throw exception
        try:
            approver_reports = FyleReportApproval.get_approver_reports(user, query_params)
        except NoPrivilegeError:
            return None

        report_url = fyle_utils.get_fyle_report_url(user.fyle_refresh_token)

        if approver_reports['count'] > 0:
            # Save current timestamp as last_successful_poll_at
            # This will fetch new reports in next poll
            report_polling_detail.last_successful_poll_at = timezone.now()
            report_polling_detail.save()

            for report in approver_reports['data']:

                employee_display_name = slack_utils.get_report_employee_display_name(slack_client, report['employee'])

                report_notification_message = report_approval_messages.get_report_approval_notification_message(
                    report,
                    employee_display_name,
                    report_url
                )

                slack_client.chat_postMessage(
                    channel=user.slack_dm_channel_id,
                    blocks=report_notification_message
                )


def process_report_approval(report_id, user_id, team_id, message_ts):

    slack_team = utils.get_or_none(Team, id=team_id)
    assertions.assert_found(slack_team, 'Slack team not registered')

    slack_client = WebClient(token=slack_team.bot_access_token)

    user = utils.get_or_none(User, slack_user_id=user_id)
    assertions.assert_found(user, 'Approver not found')

    query_params = {
        'id': 'eq.{}'.format(report_id),
        # Mandatory query params required by sdk
        'limit': 1,
        'offset': 0,
        'order': 'submitted_at.desc'
    }
    approver_report = FyleReportApproval.get_approver_reports(user, query_params)['data'][0]
    # approver_report = FyleReportApproval.get_approver_report_by_id(user, report_id)['data']

    is_report_approved, is_report_approvable, report_state_message = FyleReportApproval.check_report_approval_states(
        approver_report,
        user.fyle_employee_id
    )

    employee_display_name = slack_utils.get_report_employee_display_name(slack_client, approver_report['employee'])

    report_url = fyle_utils.get_fyle_report_url(user.fyle_refresh_token)
    report_url = '{}/{}?org_id={}'.format(report_url, approver_report['id'], approver_report['org_id'])

    if is_report_approvable is True or is_report_approved is False:

        approver_report = FyleReportApproval.approve_report(user, report_id)
        report_state_message = 'Expense report approved by you :white_check_mark:'

    report_approval_message_block = report_approval_messages.get_report_approval_notification_message(
        approver_report,
        employee_display_name,
        report_url,
        report_state_message
    )

    slack_client.chat_update(
        channel=user.slack_dm_channel_id,
        blocks=report_approval_message_block,
        ts=message_ts
    )
