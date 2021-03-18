from django.utils import timezone

from slack_sdk.web import WebClient
from fyle.platform.exceptions import NoPrivilegeError

from ...slack.ui.report_approvals.messages import get_report_approval_notification_message
from ...slack import utils as slack_utils
from ...models.report_polling_details import ReportPollingDetail
from .views import FyleReportApproval
from ...libs import logger
from .. import utils as fyle_utils


logger = logger.get_logger(__name__)


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
            'limit': 50, # Assuming no more than 50 reports will be there in 10 min poll
            'offset': 0,
            'order': 'submitted_at.desc'
        }

        # Since not all users will be approvers so the sdk api call with throw exception
        try:
            approver_reports = FyleReportApproval.get_approver_reports(user, query_params)
        except NoPrivilegeError as error:
            logger.error('Get approver reports call failed for %s - %s', user.slack_user_id, user.fyle_employee_id)
            logger.error('API call error %s ', error)
            return None

        report_url = fyle_utils.get_fyle_report_url(user.fyle_refresh_token)

        if approver_reports['count'] > 0:
            # Save current timestamp as last_successful_poll_at
            # This will fetch new reports in next poll
            report_polling_detail.last_successful_poll_at = timezone.now()
            report_polling_detail.save()

            for report in approver_reports['data']:

                employee_display_name = slack_utils.get_report_employee_display_name(slack_client, report['employee'])

                report_notification_message = get_report_approval_notification_message(
                    report,
                    employee_display_name,
                    report_url
                )

                slack_client.chat_postMessage(
                    channel=user.slack_dm_channel_id,
                    blocks=report_notification_message
                )
