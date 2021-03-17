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
    def process_report_approval():
        pass


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
