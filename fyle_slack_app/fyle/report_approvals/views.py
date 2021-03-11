import requests

from django.conf import settings
from urllib.parse import quote_plus

from ...libs import assertions
from .. import utils


class FyleReportApproval:

    @staticmethod
    def get_approver_reports(user, query_params):
        connection = utils.get_fyle_sdk_connection(user.fyle_refresh_token)
        approver_reports = connection.v1.approver.reports(query_params=query_params)
        return approver_reports


    @staticmethod
    def get_appprover_reports_from_api(access_token, approver_id, submitted_at):

        approver_reports_url = "{}/approver/reports?state=eq.APPROVER_PENDING&approvals=cs.[{{\"state\": \"APPROVAL_PENDING\", \"approver_id\": \"{}\"}}]&submitted_at=gte.{}".format(settings.FYLE_PLATFORM_URL, approver_id, quote_plus(str(submitted_at)))

        approver_reports_headers = {
            'Authorization': 'Bearer {}'.format(access_token)
        }

        approver_reports = requests.get(approver_reports_url, headers=approver_reports_headers)

        assertions.assert_good(approver_reports.status_code == 200)

        return approver_reports.json()
