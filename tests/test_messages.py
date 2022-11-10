from fyle_slack_app.slack.ui import authorization, dashboard
import os

FYLE_STOPLIGHT_URL = os.environ['FYLE_STOPLIGHT_URL']
MOCK_FYLE_OAUTH_URL = FYLE_STOPLIGHT_URL
MOCK_USERNAME = 'fake_username'

class TestAuthorizationMessages:

    def test_pre_authorization_message(self):
        pre_authorization_message = authorization.messages.get_pre_authorization_message(MOCK_USERNAME, FYLE_STOPLIGHT_URL)
        assert type(pre_authorization_message) is list

    def test_post_authorization_message(self):
        post_authorization_message = authorization.messages.get_post_authorization_message()
        assert type(post_authorization_message) is list

class TestDashboardMessages:

    def test_get_pre_authorization_message(self):
        pre_authorization_message = authorization.messages.get_pre_authorization_message(MOCK_USERNAME, MOCK_FYLE_OAUTH_URL)
        assert 'type' in pre_authorization_message[0]

    def test_get_post_authorization_message(self):
        post_authorization_message = authorization.messages.get_post_authorization_message()
        assert type(post_authorization_message) is list

    def test_get_sent_back_reports_dashboard_view(self):
        mock_reports = {
            'total_amount': 100,
            'count': 1,
            'url': MOCK_FYLE_OAUTH_URL
        }
        sent_back_reports_view = dashboard.messages.get_sent_back_reports_dashboard_view(mock_reports, 'INR')
        assert type(sent_back_reports_view) is list

    def test_get_incomplete_expenses_dashboard_view(self):
        mock_expenses = {
            'total_amount': 100,
            'count': 1,
            'url': MOCK_FYLE_OAUTH_URL
        }
        incomplete_expenses_view = dashboard.messages.get_incomplete_expenses_dashboard_view(mock_expenses, 'INR')
        assert type(incomplete_expenses_view) is list

    def test_get_unreported_expenses_dashboard_view(self):
        mock_expenses = {
            'total_amount': 100,
            'count': 1,
            'url': MOCK_FYLE_OAUTH_URL
        }
        unreported_expenses_view = dashboard.messages.get_unreported_expenses_dashboard_view(mock_expenses, 'INR')
        assert type(unreported_expenses_view) is list

    def test_get_draft_reports_dashboard_view(self):
        mock_expenses = {
            'total_amount': 100,
            'count': 1,
            'url': MOCK_FYLE_OAUTH_URL
        }
        draft_reports_view = dashboard.messages.get_draft_reports_dashboard_view(mock_expenses, 'INR')
        assert type(draft_reports_view) is list

    def test_get_dashboard_view(self):
        mock_sent_back_reports = {
            'total_amount': 100,
            'count': 1,
            'url': MOCK_FYLE_OAUTH_URL
        }
        mock_incomplete_expenses = {
            'total_amount': 100,
            'count': 1,
            'url': MOCK_FYLE_OAUTH_URL
        }
        mock_unreported_expenses = {
            'total_amount': 100,
            'count': 1,
            'url': MOCK_FYLE_OAUTH_URL
        }
        mock_draft_reports = {
            'total_amount': 100,
            'count': 1,
            'url': MOCK_FYLE_OAUTH_URL
        }
        mock_home_currency = 'INR'
        dashboard_view = dashboard.messages.get_dashboard_view(
            mock_sent_back_reports,
            mock_incomplete_expenses,
            mock_unreported_expenses,
            mock_draft_reports,
            mock_home_currency
        )
        assert type(dashboard_view['blocks']) is list