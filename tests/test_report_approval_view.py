from fyle_slack_app.fyle.report_approvals.views import FyleReportApproval
import mock
from fyle_slack_app.models import User

class TestFyleReportApproval:

    def test_get_approver_report(self, mocker, db, report_approval_user):  
        fake_return_value = [1, 2, 3]
        mocker.patch('fyle.platform.platform.v1beta.approver.reports.list', 
            return_value = fake_return_value
        )
        fyle_report_approval = FyleReportApproval(report_approval_user)
        dummy_list = fyle_report_approval.get_approver_reports(query_params={})
        return dummy_list == fake_return_value

    def test_get_report_by_id(self, mocker, db, report_approval_user):
        fake_return_value = [1, 2, 3]
        mocker.patch('fyle.platform.platform.v1beta.approver.reports.get_by_id', 
            return_value = fake_return_value
        )
        test_connection = FyleReportApproval(report_approval_user)
        dummy_list = test_connection.get_report_by_id(report_id = 'fake-report-id')
        return dummy_list == fake_return_value

    def test_get_approver_report_expenses(self, mocker, db, report_approval_user):
        fake_return_value = [1, 2, 3]
        mocker.patch('fyle.platform.platform.v1beta.approver.expenses.list', 
            return_value = fake_return_value
        )
        test_connection = FyleReportApproval(report_approval_user)
        dummy_list = test_connection.get_approver_report_expenses(query_params = {})
        return dummy_list == fake_return_value

    def test_approve_report(self, mocker, db, report_approval_user):
        fake_return_value = [1, 2, 3]
        mocker.patch('fyle.platform.platform.v1beta.approver.reports.approve', 
            return_value = fake_return_value
        )
        test_connection = FyleReportApproval(report_approval_user)
        dummy_list = test_connection.approve_report(report_id = 'fake-report-id')
        return dummy_list == fake_return_value

    def test_can_approve_report(self):

        # test if report.state == 'APPROVER_INQUIRY'
        fake_report = {
            'state' : 'APPROVER_INQUIRY'
        }
        FAKE_APPROVER_USER_ID = 'fake-approver-user-id'
        can_approve_report, report_message = FyleReportApproval.can_approve_report(fake_report, FAKE_APPROVER_USER_ID)
        assert can_approve_report == False and report_message == 'This expense report has been sent back to the employee'

        # test if report.state in report_approved_states
        fake_report = {
            'state': 'PAYMENT_PROCESSING'
        }
        can_approve_report, report_message = FyleReportApproval.can_approve_report(fake_report, FAKE_APPROVER_USER_ID)
        assert can_approve_report == False and report_message == 'This expense report has already been approved :white_check_mark:'

        fake_report = {
            'state':'OTHER',
            'approvals':[
                {
                    'approver_user_id':FAKE_APPROVER_USER_ID,
                    'state': 'APPROVAL_DONE'
                }
            ]
        }
        can_approve_report, report_message = FyleReportApproval.can_approve_report(fake_report, FAKE_APPROVER_USER_ID)
        assert can_approve_report == False and report_message == 'Looks like you\'ve already approved this expense report :see_no_evil:'

        fake_report = {
            'state':'OTHER',
            'approvals':[
                {
                    'approver_user_id':FAKE_APPROVER_USER_ID,
                    'state': 'APPROVAL_DISABLED'
                }
            ]
        }
        can_approve_report, report_message = FyleReportApproval.can_approve_report(fake_report, FAKE_APPROVER_USER_ID)
        assert can_approve_report == False and report_message == 'Looks like you no longer have permission to approve this expense report :see_no_evil:'

    def test_track_report_approval(self, mocker, db):
        user = mock.Mock(spec = User)
        user.email = 'fake-email@gmail.com'
        mocker.patch('fyle_slack_app.fyle.notifications.views.FyleNotificationView.get_report_tracking_data', return_value = dict())
        mocker.patch('fyle_slack_app.tracking.identify_user', return_value = None)
        mocker.patch('fyle_slack_app.tracking.track_event', return_value = True)
        FyleReportApproval.track_report_approved(user, report = {}, modal = True)
