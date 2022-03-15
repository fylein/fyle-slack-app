from typing import Dict, Tuple

from fyle.platform.platform import Platform

from fyle_slack_app import tracking
from fyle_slack_app.models.users import User
from fyle_slack_app.fyle import utils as fyle_utils
from fyle_slack_app.fyle.notifications.views import FyleNotificationView


class FyleReportApproval:

    connection: Platform = None

    def __init__(self, user: User) -> None:
        self.connection = fyle_utils.get_fyle_sdk_connection(user.fyle_refresh_token)


    def get_approver_reports(self, query_params: Dict) -> Dict:
        approver_reports = self.connection.v1beta.approver.reports.list(query_params=query_params)
        return approver_reports


    def get_report_by_id(self, report_id: str) -> Dict:
        approver_report = self.connection.v1beta.approver.reports.get_by_id(report_id)
        return approver_report


    def get_approver_report_expenses(self, query_params: dict) -> Dict:
        approver_report_expenses = self.connection.v1beta.approver.expenses.list(query_params=query_params)
        return approver_report_expenses


    def approve_report(self, report_id: str) -> Dict:
        approved_report = self.connection.v1beta.approver.reports.approve(report_id)
        return approved_report


    @staticmethod
    def can_approve_report(report: Dict, approver_user_id: str) -> Tuple[bool, str]:

        report_approved_states = ['APPROVED', 'PAYMENT_PENDING', 'PAYMENT_PROCESSING', 'PAID']

        report_message = None
        can_approve_report = True

        if report['state'] == 'APPROVER_INQUIRY':
            can_approve_report = False
            report_message = 'This expense report has been sent back to the employee'

        elif report['state'] in report_approved_states:
            can_approve_report = False
            report_message = 'This expense report has already been approved :white_check_mark:'

        elif can_approve_report is True:

            for approver in report['approvals']:

                if approver['approver_user_id'] == approver_user_id:

                    if approver['state'] == 'APPROVAL_DONE':
                        can_approve_report = False
                        report_message = 'Looks like you\'ve already approved this expense report :see_no_evil:'
                        break

                    if approver['state'] == 'APPROVAL_DISABLED':
                        can_approve_report = False
                        report_message = 'Looks like you no longer have permission to approve this expense report :see_no_evil:'
                        break

        return can_approve_report, report_message


    @staticmethod
    def track_report_approved(user: User, report: Dict, modal: bool = False) -> None:
        event_data = FyleNotificationView.get_report_tracking_data(user, report)

        tracking.identify_user(user.email)

        if modal is True:
            tracking.track_event(user.email, 'Report Approved From Slack Modal', event_data)
        else:
            tracking.track_event(user.email, 'Report Approved From Slack', event_data)
