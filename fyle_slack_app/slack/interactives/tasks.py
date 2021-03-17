from fyle_slack_app.fyle.utils import get_cluster_domain, get_fyle_access_token
from slack_sdk.web.client import WebClient

from ...slack.utils import get_report_employee_display_name
from ...libs import utils, assertions
from ...fyle.report_approvals.views import FyleReportApproval
from ...models import User, Team
from ..ui.report_approvals import messages as report_approval_messages


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

    report_approved_states = ['PAYMENT_PENDING', 'APPROVED', 'PAYMENT_PROCESSING', 'PAID']

    is_report_approved = False
    is_report_approvable = True

    if approver_report['state'] == 'APPROVER_INQUIRY':
        is_report_approvable = False
        message = 'This report can\'t be approved as it is sent back to the employee :x:'

    if approver_report['state'] in report_approved_states and is_report_approvable is True:
        is_report_approved = True
        message = 'This report is already approved :white_check_mark:'

    if is_report_approved is False and is_report_approvable is True:

        for approver in approver_report['approvals']:

            if approver['approver_id'] == user.fyle_employee_id:

                if approver['state'] == 'APPROVAL_DONE':
                    is_report_approved = True
                    message = 'This report is already approved by you :white_check_mark:'

                if approver['state'] == 'APPROVAL_DISABLED':
                    is_report_approvable = False
                    message = 'Your approval is disabled on this report :x:'

    employee_display_name = get_report_employee_display_name(slack_client, approver_report['employee'])

    report_section_block = report_approval_messages.get_report_section_blocks(
        approver_report,
        employee_display_name
    )

    access_token = get_fyle_access_token(user.fyle_refresh_token)
    cluster_domain = get_cluster_domain(access_token)

    # pylint: disable=line-too-long
    REPORT_URL = '{}/app/main/#/enterprise/reports/{}?org_id={}'.format(cluster_domain, approver_report['id'], approver_report['org_id'])

    report_view_in_fyle_section = report_approval_messages.get_report_review_in_fyle_action(REPORT_URL, 'View in Fyle')

    if is_report_approvable is False or is_report_approved is True:
        message_section = {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': message
            }
        }

        report_section_block.append(message_section)
        report_section_block.append(report_view_in_fyle_section)

        slack_client.chat_update(
            channel=user.slack_dm_channel_id,
            blocks=report_section_block,
            ts=message_ts
        )
