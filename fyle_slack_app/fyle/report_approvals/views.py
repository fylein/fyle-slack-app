from django.utils import timezone

from ...models import ReportPollingDetail
from ...libs import utils


class FyleReportApproval:

    @staticmethod
    def get_approver_reports(user, query_params):
        connection = utils.get_fyle_sdk_connection(user.fyle_refresh_token)
        approver_reports = connection.v1.approver.reports(query_params=query_params)
        return approver_reports


    @staticmethod
    def get_or_create_report_polling_detail(user):
        report_polling_detail = utils.get_or_none(ReportPollingDetail, user=user)

        if report_polling_detail is None:
            report_polling_detail = ReportPollingDetail.objects.create(
                user=user,
                last_successful_poll_at=timezone.now()
            )

        return report_polling_detail