from django.utils import timezone

from django_q.models import Schedule

from slack_sdk.web import WebClient
from fyle.platform.exceptions import NoPrivilegeError

from ...slack.ui.report_approvals.messages import get_report_approval_notification_message
from ...slack import utils as slack_utils
from ...models.report_polling_details import ReportPollingDetail
from .views import FyleReportApproval
from .. import utils as fyle_utils


# Schedule report polling task to run every 10 mins
def schedule_report_approval_polling():
    # Info on `get_or_create` method -> https://simpleisbetterthancomplex.com/tips/2016/07/14/django-tip-6-get-or-create.html
    Schedule.objects.get_or_create(
        func='fyle_slack_app.fyle.report_approvals.tasks.poll_report_approvals',
        schedule_type=Schedule.CRON,
        cron='*/10 * * * *'
        # Use '*/1 * * * *' for testing -> cron to run every minute
        # Use '*/10 * * * *' for actual 10 min cron
    )


def poll_report_approvals():
    # select_related joins the two table with foriegn key column
    # `__slack_team` joins `users` table with `teams` table
    report_polling_details = ReportPollingDetail.objects.select_related('user__slack_team').all()

    for report_polling_detail in report_polling_details:
        user = report_polling_detail.user

        slack_client = WebClient(token=user.slack_team.bot_access_token)

        approver_id = user.fyle_employee_id

        # Fetch approver reports to approve - i.e. report state -> APPROVER_PENDING & approval state -> APPROVAL_PENDING
        query_params = {
            'state': 'eq.APPROVER_PENDING',
            'approvals': 'cs.[{{ "approver_id": {}, "state": "APPROVAL_PENDING" }}]'.format(approver_id),
            'submitted_at': 'gte.{}'.format(str(report_polling_detail.last_successful_poll_at)),

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

        fyle_access_token = fyle_utils.get_fyle_access_token(user.fyle_refresh_token)

        # Cluster domain for view report url
        cluster_domain = fyle_utils.get_cluster_domain(fyle_access_token)

        if approver_reports['count'] > 0:
            # Save current timestamp as last_successful_poll_at
            # This will fetch new reports in next poll
            report_polling_detail.last_successful_poll_at = timezone.now()
            report_polling_detail.save()

            for report in approver_reports['data']:

                employee_display_name = slack_utils.get_report_employee_display_name(slack_client, report['employee'])

                report_notification_message = get_report_approval_notification_message(report, employee_display_name, cluster_domain)

                slack_client.chat_postMessage(
                    channel=user.slack_dm_channel_id,
                    blocks=report_notification_message
                )
