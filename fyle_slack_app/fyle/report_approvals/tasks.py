from django.utils import timezone

from django_q.tasks import schedule
from django_q.models import Schedule

from slack_sdk.web import WebClient

from ...slack.ui.report_approvals.messages import get_report_approval_notification_message
from ...libs import utils
from ...models import User
from .views import FyleReportApproval


def schedule_report_approval_polling():
    # Schedule report polling task to run every 10 mins
    task_function_path = 'fyle_slack_app.fyle.report_approvals.tasks.poll_report_approvals'
    report_polling_schedule = utils.get_or_none(Schedule, func=task_function_path)

    if report_polling_schedule is None:
        schedule(
            task_function_path,
            schedule_type=Schedule.CRON,
            cron='*/10 * * * *' # Use '*/1 * * * *' for testing -> cron to run every minute
        )


def poll_report_approvals():
    # select_related joins the two table with foriegn key column
    users = User.objects.select_related('slack_team').all()

    for user in users:
        slack_client = WebClient(token=user.slack_team.bot_access_token)

        report_polling_detail = FyleReportApproval.get_or_create_report_polling_detail(user)

        # Fetch approver reports to approve
        # Try except because not all users will be approver
        # So sdk may throw error incase of users who are not approvers
        # try:
        #     report_details = FyleReportApproval.get_approver_reports(user, 'APPROVAL_PENDING')
        # except:
        #     return True

        report_details = {
                "count": 10000,
                "offset": 10,
                "data": [
                    {
                    "id": "sdfd2391",
                    "org_id": "orwruogwnngg",
                    "created_at": "2020-06-01T13:14:54.804+00:00",
                    "updated_at": "2020-06-11T13:14:55.201598+00:00",
                    "employee_id": "sdfd2391",
                    "employee": {
                        "id": "sdfd2391",
                        "user": {
                            "email": "john.doe@example.com",
                            "full_name": "John Doe"
                        },
                        "code": "E84122"
                    },
                    "purpose": "Business trip to London",
                    "currency": "INR",
                    "amount": 47.99,
                    "tax": 47.99,
                    "state": "DRAFT",
                    "num_expenses": 3,
                    "is_manually_flagged": True,
                    "is_policy_flaged": True,
                    "reimbursed_at": "2020-06-11T13:14:55.201598+00:00",
                    "approved_at": "2020-06-11T13:14:55.201598+00:00",
                    "submitted_at": "2020-06-11T13:14:55.201598+00:00",
                    "claim_number": "C/2021/02/R/907",
                    "source": "string",
                    "approvals": [
                        {
                        "approver_id": "sdfd2391",
                        "approver": {
                            "id": "sdfd2391",
                            "user": {
                            "email": "john.doe@example.com",
                            "full_name": "John Doe"
                            },
                            "code": "E84122"
                        },
                        "state": "APPROVAL_PENDING"
                        }
                    ]
                }
            ]
        }

        if report_details['count'] > 0:
            # TODO: .save() save updated data to db
            # This might not be the right place to do this operation

            # Save current timestamp as last_successful_poll_at
            # This will fetch new reports in next poll
            report_polling_detail.last_successful_poll_at = timezone.now()
            report_polling_detail.save()

            for report in report_details['data']:
                report_notification_message = get_report_approval_notification_message(report)

                # slack_client.chat_postMessage(
                #     channel=user.slack_dm_channel_id,
                #     blocks=report_notification_message
                # )

                # Hardcoded for testing
                slack_client.chat_postMessage(
                    channel='D01K1L9UHBP',
                    blocks=report_notification_message
                )
