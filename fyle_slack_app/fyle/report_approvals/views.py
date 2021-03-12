import requests

from django.conf import settings
from urllib.parse import quote_plus

from ...libs import assertions
from .. import utils


class FyleReportApproval:

    @staticmethod
    def get_approver_reports(user, query_params):
        connection = utils.get_fyle_sdk_connection(user.fyle_refresh_token)
        approver_reports = connection.v1.approver.reports.list(query_params=query_params)
        return approver_reports
