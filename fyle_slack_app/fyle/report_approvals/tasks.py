from django.utils import timezone

from django_q.tasks import schedule
from django_q.models import Schedule

from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError

from ...slack.ui.report_approvals.messages import get_report_approval_notification_message
from ...libs import utils
from ...models.report_polling_details import ReportPollingDetail
from .views import FyleReportApproval


# Schedule report polling task to run every 10 mins
def schedule_report_approval_polling():
    # Info on `get_or_create` method -> https://simpleisbetterthancomplex.com/tips/2016/07/14/django-tip-6-get-or-create.html
    Schedule.objects.get_or_create(
        func='fyle_slack_app.fyle.report_approvals.tasks.poll_report_approvals',
        schedule_type=Schedule.CRON,
        cron='*/10 * * * *' # User '*/10 * * * *' for testing -> cron to run every minute
    )


def get_report_employee_message(slack_client, employee_details):
    try:
        user_info = slack_client.users_lookupByEmail(email=employee_details['user']['email'])
        employee_message = '<@{}>'.format(user_info['user']['id'])
    except SlackApiError:
        employee_message = employee_details['user']['full_name']

    return employee_message


def poll_report_approvals():
    # select_related joins the two table with foriegn key column
    # `__slack_team` joins `users` table with `teams` table
    report_polling_details = ReportPollingDetail.objects.select_related('user__slack_team').all()

    for report_polling_detail in report_polling_details:
        user = report_polling_detail.user

        slack_client = WebClient(token=user.slack_team.bot_access_token)

        report_polling_detail = FyleReportApproval.get_or_create_report_polling_detail(user)

        approver_id = 'ouUW6KWYLMq6'

        # Fetch approver reports to approve
        query_params = {
            'approvals': 'cs.[{"approver_id": {}, "state": {}}]'.format(approver_id, 'APPROVAL_PENDING'),
            'submitted_at': 'gte.{}'.format(report_polling_detail.last_successful_poll_at)
        }
        approver_reports = FyleReportApproval.get_approver_reports(user, query_params)

        # approver_reports = {
        #         "count": 10000,
        #         "offset": 10,
        #         "data": [
        #             {
        #             "id": "sdfd2391",
        #             "org_id": "orwruogwnngg",
        #             "created_at": "2020-06-01T13:14:54.804+00:00",
        #             "updated_at": "2020-06-11T13:14:55.201598+00:00",
        #             "employee_id": "sdfd2391",
        #             "employee": {
        #                 "id": "sdfd2391",
        #                 "user": {
        #                     "email": "shreyanshss7@gmail.com",
        #                     "full_name": "John Doe"
        #                 },
        #                 "code": "E84122"
        #             },
        #             "purpose": "Business trip to London",
        #             "currency": "INR",
        #             "amount": 47.99,
        #             "tax": 47.99,
        #             "state": "APPROVER_PENDING",
        #             "num_expenses": 3,
        #             "is_manually_flagged": True,
        #             "is_policy_flaged": True,
        #             "reimbursed_at": "2020-06-11T13:14:55.201598+00:00",
        #             "approved_at": "2020-06-11T13:14:55.201598+00:00",
        #             "submitted_at": "2020-06-11T13:14:55.201598+00:00",
        #             "claim_number": "C/2021/02/R/907",
        #             "source": "string",
        #             "approvals": [
        #                 {
        #                 "approver_id": "sdfd2391",
        #                 "approver": {
        #                     "id": "sdfd2391",
        #                     "user": {
        #                     "email": "john.doe@example.com",
        #                     "full_name": "John Doe"
        #                     },
        #                     "code": "E84122"
        #                 },
        #                 "state": "APPROVAL_PENDING"
        #                 }
        #             ]
        #         }
        #     ]
        # }

        # approver_id = 'sdfd2391'

        if approver_reports['count'] > 0:
            # TODO: .save() save updated data to db
            # This might not be the right place to do this operation

            # Save current timestamp as last_successful_poll_at
            # This will fetch new reports in next poll
            report_polling_detail.last_successful_poll_at = timezone.now()
            report_polling_detail.save()

            for report in approver_reports['data']:

                employee_message = get_report_employee_message(slack_client, report['employee'])

                report_notification_message = get_report_approval_notification_message(report, approver_id, employee_message)

                slack_client.chat_postMessage(
                    channel=user.slack_dm_channel_id,
                    blocks=report_notification_message
                )

                # Hardcoded for testing
                # slack_client.chat_postMessage(
                #     channel='D01K1L9UHBP',
                #     blocks=report_notification_message
                # )
