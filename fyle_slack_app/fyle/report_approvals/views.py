from typing import Dict, Tuple

from fyle_slack_app import tracking
from fyle_slack_app.models.users import User
from fyle_slack_app.fyle import utils as fyle_utils


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
    def get_tracking_event_data(user: User, report: Dict) -> Dict:
        event_data = {
            'asset': 'SLACK_APP',
            'slack_user_id': user.slack_user_id,
            'fyle_user_id': user.fyle_user_id,
            'email': user.email,
            'slack_team_id': user.slack_team.id,
            'slack_team_name': user.slack_team.name,
            'report_id': report['id'],
            'org_id': report['org_id']
        }

        return event_data

    @staticmethod
    def track_report_notification_received(user: User, report: Dict) -> None:
        event_data = FyleReportApproval.get_tracking_event_data(user, report)

        tracking.identify_user(user.email)

        tracking.track_event(user.email, 'Report Approval Notification Received', event_data)


    @staticmethod
    def track_report_approved(user: User, report: Dict) -> None:
        event_data = FyleReportApproval.get_tracking_event_data(user, report)

        tracking.identify_user(user.email)

        tracking.track_event(user.email, 'Report Approved From Slack', event_data)


    @staticmethod
    def track_report_reviewed_in_fyle(user: User, report: Dict) -> None:
        event_data = FyleReportApproval.get_tracking_event_data(user, report)

        tracking.identify_user(user.email)

        tracking.track_event(user.email, 'Report Reviewed In Fyle', event_data)
