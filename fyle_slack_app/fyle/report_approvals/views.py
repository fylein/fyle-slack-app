from typing import Dict, Tuple

import json
import croniter

from django.http import JsonResponse, HttpRequest
from django.views.generic.base import View
from django.contrib.auth import authenticate

from django_q.models import Schedule

from fyle_slack_app.models.users import User
from fyle_slack_app.fyle import utils as fyle_utils
from fyle_slack_app.libs import assertions


class FyleReportApproval:

    @staticmethod
    def get_approver_reports(user: User, query_params: Dict) -> Dict:
        connection = fyle_utils.get_fyle_sdk_connection(user.fyle_refresh_token)
        approver_reports = connection.v1.approver.reports.list(query_params=query_params)
        return approver_reports


    @staticmethod
    def get_report_by_id(user: User, report_id: str) -> Dict:
        connection = fyle_utils.get_fyle_sdk_connection(user.fyle_refresh_token)
        approver_report = connection.v1.approver.reports.get(report_id)
        return approver_report


    @staticmethod
    def approve_report(user: User, report_id: str) -> Dict:
        connection = fyle_utils.get_fyle_sdk_connection(user.fyle_refresh_token)
        approved_report = connection.v1.approver.reports.approve(report_id)
        return approved_report


    @staticmethod
    def can_approve_report(report: Dict, approver_user_id: str) -> Tuple[bool, str]:

        report_approved_states = ['APPROVED', 'PAYMENT_PENDING', 'PAYMENT_PROCESSING', 'PAID']

        report_message = None
        can_approve_report = True

        if report['state'] == 'APPROVER_INQUIRY':
            can_approve_report = False
            report_message = 'This expense report can\'t be approved as it is sent back to the employee :x:'

        elif report['state'] in report_approved_states:
            can_approve_report = False
            report_message = 'This expense report is already approved :white_check_mark:'

        elif can_approve_report is True:

            for approver in report['approvals']:

                if approver['approver_user_id'] == approver_user_id:

                    if approver['state'] == 'APPROVAL_DONE':
                        can_approve_report = False
                        report_message = 'This expense report is already approved by you :white_check_mark:'
                        break

                    if approver['state'] == 'APPROVAL_DISABLED':
                        can_approve_report = False
                        report_message = 'Your approval is disabled on this expense report :x:'
                        break

        return can_approve_report, report_message


class FyleReportPolling(View):

    # Endpoint to trigger the background cron task for report polling
    # Since this is an endpoint we'll need to protect this
    # Only django's superuser will be able to create the cron task
    def post(self, request: HttpRequest) -> JsonResponse:
        payload = json.loads(request.body)
        superuser_username = payload['superuser_username']
        superuser_password = payload['superuser_password']

        superuser = authenticate(username=superuser_username, password=superuser_password)
        assertions.assert_found(superuser, 'Invalid superuser credentials')
        assertions.assert_true(superuser.is_superuser)

        cron_expression = payload['cron_expression']
        assertions.assert_valid(croniter.croniter.is_valid(cron_expression), 'Invalid cron expression')

        # Info on `get_or_create` method
        # https://simpleisbetterthancomplex.com/tips/2016/07/14/django-tip-6-get-or-create.html
        Schedule.objects.get_or_create(
            func='fyle_slack_app.fyle.report_approvals.tasks.poll_report_approvals',
            schedule_type=Schedule.CRON,
            cron=cron_expression
            # Use '*/1 * * * *' for testing -> cron to run every minute
            # Use '*/10 * * * *' for 10 min cron
        )
        return JsonResponse({'message': 'Report polling task scheduled'})
