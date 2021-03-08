from django.utils import timezone

from ...models import ReportPollingDetail
from ...libs import utils


class FyleReportApproval:

    @staticmethod
    def get_approver_reports(user, state):
        connection = utils.get_fyle_sdk_connection(user.fyle_refresh_token)

        user_profile_details = connection.v1.fyler.my_profile()
        approver_id = user_profile_details['data']['employee_id']

        report_details = connection.v1.approver.report_approvals(query_params={
            'approvals': 'cs.[{"approver_id": {}, "state": {}}]'.format(approver_id, state)
        })
        return report_details


    @staticmethod
    def get_or_create_report_polling_detail(user):
        report_polling_detail = utils.get_or_none(ReportPollingDetail, user=user)

        if report_polling_detail is None:
            report_polling_detail = ReportPollingDetail.objects.create(
                user=user,
                last_successful_poll_at=timezone.now()
            )

        return report_polling_detail