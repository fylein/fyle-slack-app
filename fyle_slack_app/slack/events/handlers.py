from typing import Callable, Dict, Tuple

from datetime import timedelta

from fyle.platform import Platform

from django.http import JsonResponse
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from django_q.tasks import schedule, async_task
from django_q.models import Schedule

from fyle_slack_app.models import User
from fyle_slack_app.fyle.utils import get_fyle_oauth_url, get_fyle_profile, get_fyle_sdk_connection
from fyle_slack_app.libs import utils, assertions, logger
from fyle_slack_app.slack.ui.dashboard import messages
from fyle_slack_app.slack import utils as slack_utils


logger = logger.get_logger(__name__)


class SlackEventHandler:

    _event_callback_handlers: Dict = {}

    def _initialize_event_callback_handlers(self):
        self._event_callback_handlers = {
            'team_join': self.handle_new_user_joined,
            'app_home_opened': self.handle_app_home_opened,
            'app_uninstalled': self.handle_app_uninstalled,
            'file_shared': self.handle_file_shared
        }


    def handle_invalid_event(self, slack_payload: Dict, team_id: str) -> JsonResponse:
        # No need to send any message to user in this case
        # Slack sends some message event whenever a message is sent to slack
        # Ex: Pre auth message
        # Since we're not interested in that & it will call this function to be invoked
        # So, do nothing in those cases
        return JsonResponse({}, status=200)


    def handle_event_callback(self, event_type: str, slack_payload: Dict, team_id: str) -> Callable:

        logger.info('Slack Event Received -> %s', event_type)

        self._initialize_event_callback_handlers()

        handler = self._event_callback_handlers.get(event_type, self.handle_invalid_event)

        return handler(slack_payload, team_id)


    def handle_app_uninstalled(self, slack_payload: Dict, team_id: str) -> JsonResponse:

        # Deleting team details in background task
        async_task(
            'fyle_slack_app.slack.events.tasks.uninstall_app',
            team_id
        )

        response = JsonResponse({}, status=200)

        # Passing this for slack not to retry `app_uninstalled` event again
        response['X-Slack-No-Retry'] = 1

        return response


    def handle_new_user_joined(self, slack_payload: Dict, team_id: str) -> None:
        user_id = slack_payload['event']['user']['id']
        schedule('fyle_slack_app.slack.events.tasks.new_user_joined_pre_auth_message',
                 user_id,
                 team_id,
                 schedule_type=Schedule.ONCE,
                 next_run=timezone.now() + timedelta(days=7)
                )


    def handle_app_home_opened(self, slack_payload: Dict, team_id: str) -> JsonResponse:
        user_id = slack_payload['event']['user']
        user = utils.get_or_none(User, slack_user_id=user_id)

        slack_client = slack_utils.get_slack_client(team_id)

        # User is not present i.e. user hasn't done Fyle authorization
        if user is not None:
            platform = get_fyle_sdk_connection(user.fyle_refresh_token)
            spender_profile = get_fyle_profile(user.fyle_refresh_token)
            home_currency = spender_profile['org']['currency']
            sent_back_reports, draft_reports = self.get_sent_back_and_draft_reports(platform, user_id)
            unreported_expenses, incomplete_expenses = self.get_unreported_and_incomplete_expenses(platform, user_id)

            dashboard_view = messages.get_dashboard_view(
                sent_back_reports=sent_back_reports,
                incomplete_expenses=incomplete_expenses,
                unreported_expenses=unreported_expenses,
                draft_reports=draft_reports,
                home_currency=home_currency
            )
        else:
            user_info = slack_client.users_info(user=user_id)
            assertions.assert_good(user_info['ok'] is True)

            fyle_oauth_url = get_fyle_oauth_url(user_id, team_id)

            dashboard_view = messages.get_pre_authorization_message(user_info['user']['real_name'], fyle_oauth_url)

        slack_client.views_publish(user_id=user_id, view=dashboard_view)

        return JsonResponse({}, status=200)


    def handle_file_shared(self, slack_payload: Dict, team_id: str) -> JsonResponse:
        file_id = slack_payload['event']['file_id']
        user_id = slack_payload['event']['user_id']

        async_task(
            'fyle_slack_app.slack.events.tasks.handle_file_shared',
            file_id,
            user_id,
            team_id
        )

        response = JsonResponse({}, status=200)
        # Passing this for slack not to retry `file_shared` event again
        response['X-Slack-No-Retry'] = 1

        return response


    def get_sent_back_and_draft_reports(self, platform: Platform, user_id: str) -> Tuple[Dict, Dict]:
        sent_back_and_draft_reports = cache.get(f'{user_id}.sent_back_and_draft_reports')

        if sent_back_and_draft_reports is None:
            sent_back_and_draft_reports = platform.v1.spender.reports.list(query_params={
                'limit': 100,
                'offset': 0,
                'order': 'created_at.desc',
                'or': '(state.eq.APPROVER_INQUIRY,state.eq.DRAFT)'
            })
            cache.set(f'{user_id}.sent_back_and_draft_reports', sent_back_and_draft_reports, 300)

        sent_back_reports = list(filter(lambda report: report['state'] == 'APPROVER_INQUIRY', sent_back_and_draft_reports['data']))
        if len(sent_back_reports) > 0:
            url = '{}/app/main/#/my_reports/'.format(settings.FYLE_APP_URL)
            total_amount = sum(report['amount'] for report in sent_back_reports)
            sent_back_reports = {
                'total_amount': total_amount,
                'count': len(sent_back_reports),
                'url': utils.convert_to_branchio_url(url, {'state': 'inquiry'})
            }
        else:
            sent_back_reports = None

        draft_reports = list(filter(lambda report: report['state'] == 'DRAFT', sent_back_and_draft_reports['data']))
        if len(draft_reports) > 0:
            url = '{}/app/main/#/my_reports/'.format(settings.FYLE_APP_URL)
            total_amount = sum(report['amount'] for report in draft_reports)
            draft_reports = {
                'total_amount': total_amount,
                'count': len(draft_reports),
                'url': utils.convert_to_branchio_url(url, {'state': 'draft'})
            }
        else:
            draft_reports = None

        return sent_back_reports, draft_reports


    def get_unreported_and_incomplete_expenses(self, platform: Platform, user_id: str) -> Tuple[Dict, Dict]:
        incomplete_and_unreported_expenses = cache.get(f'{user_id}.incomplete_and_unreported_expenses')

        if incomplete_and_unreported_expenses is None:
            incomplete_and_unreported_expenses = platform.v1.spender.expenses.list(query_params={
                'limit': 100,
                'offset': 0,
                'order': 'created_at.desc',
                'or': '(state.eq.COMPLETE,state.eq.DRAFT)'
            })
            cache.set(f'{user_id}.incomplete_and_unreported_expenses', incomplete_and_unreported_expenses, 300)

        incomplete_expenses = list(filter(lambda expense: expense['state'] == 'DRAFT', incomplete_and_unreported_expenses['data']))

        if len(incomplete_expenses) > 0:
            url = '{}/app/main/#/my_expenses/'.format(settings.FYLE_APP_URL)
            total_amount = sum(filter(None, (expense['amount'] for expense in incomplete_expenses)))
            incomplete_expenses = {
                'total_amount': total_amount,
                'count': len(incomplete_expenses),
                'url': utils.convert_to_branchio_url(url, {'state': 'draft'})
            }
        else:
            incomplete_expenses = None

        unreported_expenses = list(filter(lambda expense: expense['state'] == 'COMPLETE', incomplete_and_unreported_expenses['data']))

        if len(unreported_expenses) > 0:
            url = '{}/app/main/#/my_expenses/'.format(settings.FYLE_APP_URL)
            total_amount = sum(expense['amount'] for expense in unreported_expenses)
            unreported_expenses = {
                'total_amount': total_amount,
                'count': len(unreported_expenses),
                'url': utils.convert_to_branchio_url(url)
            }
        else:
            unreported_expenses = None

        return unreported_expenses, incomplete_expenses
