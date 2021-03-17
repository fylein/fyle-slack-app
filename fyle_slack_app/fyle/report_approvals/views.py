import json
import croniter

from django.http.response import JsonResponse
from django.views.generic.base import View
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.utils.decorators import method_decorator

from django_q.models import Schedule

from .. import utils as fyle_utils
from ...libs import assertions


class FyleReportApproval:

    @staticmethod
    def get_approver_reports(user, query_params):
        connection = fyle_utils.get_fyle_sdk_connection(user.fyle_refresh_token)
        approver_reports = connection.v1.approver.reports.list(query_params=query_params)
        return approver_reports


    @staticmethod
    def get_approver_report_by_id(user, report_id):
        connection = fyle_utils.get_fyle_sdk_connection(user.fyle_refresh_token)
        approver_report = connection.v1.approver.reports.get(report_id)
        return approver_report


    @staticmethod
    def check_report_approval_states(report, approver_id):

        report_approved_states = ['PAYMENT_PENDING', 'APPROVED', 'PAYMENT_PROCESSING', 'PAID']

        is_report_approved = False
        is_report_approvable = True

        if report['state'] == 'APPROVER_INQUIRY':
            is_report_approvable = False
            message = 'This report can\'t be approved as it is sent back to the employee :x:'

        if report['state'] in report_approved_states and is_report_approvable is True:
            is_report_approved = True
            message = 'This report is already approved :white_check_mark:'

        if is_report_approved is False and is_report_approvable is True:

            for approver in report['approvals']:

                if approver['approver_id'] == approver_id:

                    if approver['state'] == 'APPROVAL_DONE':
                        is_report_approved = True
                        message = 'This report is already approved by you :white_check_mark:'

                    if approver['state'] == 'APPROVAL_DISABLED':
                        is_report_approvable = False
                        message = 'Your approval is disabled on this report :x:'

        return is_report_approved, is_report_approvable, message


class FyleReportPolling(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    # Endpoint to trigger the background cron task for report polling
    # Since this is an endpoint we'll need to protect this
    # Only django's superuser will be able to create the cron task
    def post(self, request):
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
