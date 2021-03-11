from django.utils import timezone

from django_q.models import Schedule

from slack_sdk.web import WebClient

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
        cron='*/1 * * * *'
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

        # Fetch approver reports to approve
        query_params = {
            'approvals': 'cs.[{{ "approver_id": {}, "state": {} }}]'.format(approver_id, 'APPROVAL_PENDING'),
            'submitted_at': 'gte.{}'.format(str(report_polling_detail.last_successful_poll_at))
        }
        # approver_reports = FyleReportApproval.get_approver_reports(user, query_params)

        fyle_access_token = fyle_utils.get_fyle_access_token(user.fyle_refresh_token)

        approver_reports = FyleReportApproval.get_appprover_reports_from_api(fyle_access_token, approver_id, report_polling_detail.last_successful_poll_at)

        # Cluster domain for view report url
        cluster_domain = fyle_utils.get_cluster_domain(fyle_access_token)

        if approver_reports['count'] > 0:
            # TODO: .save() save updated data to db
            # This might not be the right place to do this operation

            # Save current timestamp as last_successful_poll_at
            # This will fetch new reports in next poll
            report_polling_detail.last_successful_poll_at = timezone.now()
            report_polling_detail.save()

            for report in approver_reports['data']:
                for approval in report['approvals']:
                    if approval['approver_id'] == approver_id:
                        # Send messsage only if report and approval states are below mentioned states
                        if report['state'] == 'APPROVER_PENDING' and approval['state'] == 'APPROVAL_PENDING':

                            employee_display_name = slack_utils.get_report_employee_display_name(slack_client, report['employee'])

                            report_notification_message = get_report_approval_notification_message(report, employee_display_name, cluster_domain)

                            slack_client.chat_postMessage(
                                channel=user.slack_dm_channel_id,
                                blocks=report_notification_message
                            )
