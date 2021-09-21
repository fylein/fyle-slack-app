from typing import Callable, Dict

from django.http import JsonResponse

from django_q.tasks import async_task

from fyle_slack_app.fyle.expenses.views import FyleExpense
from fyle_slack_app.fyle.utils import get_fyle_profile
from fyle_slack_app.models import User, NotificationPreference
from fyle_slack_app.models.notification_preferences import NotificationType
from fyle_slack_app.libs import assertions, utils, logger
from fyle_slack_app.slack.utils import get_slack_user_dm_channel_id, get_slack_client
from fyle_slack_app.slack.ui.expenses import messages as expense_messages
from fyle_slack_app import tracking


logger = logger.get_logger(__name__)


class BlockActionHandler:

    _block_action_handlers: Dict = {}

    # Maps action_id with it's respective function
    def _initialize_block_action_handlers(self):
        self._block_action_handlers = {
            'link_fyle_account': self.link_fyle_account,
            'review_report_in_fyle': self.review_report_in_fyle,
            'expense_view_in_fyle': self.expense_view_in_fyle,
            'approve_report': self.approve_report,
            'pre_auth_message_approve': self.handle_pre_auth_mock_button,
            'pre_auth_message_view_in_fyle': self.handle_pre_auth_mock_button,
            'report_submitted_notification_preference': self.handle_notification_preference_selection,
            'report_partially_approved_notification_preference': self.handle_notification_preference_selection,
            'report_payment_processing_notification_preference': self.handle_notification_preference_selection,
            'report_approver_sendback_notification_preference': self.handle_notification_preference_selection,
            'report_paid_notification_preference': self.handle_notification_preference_selection,
            'report_commented_notification_preference': self.handle_notification_preference_selection,
            'expense_commented_notification_preference': self.handle_notification_preference_selection,

            # Dynamic options
            'category': self.handle_category_select,
            'project': self.handle_project_select,
            # 'currency': self.handle_currency_select
        }


    # Gets called when function with an action is not found
    def _handle_invalid_block_actions(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        slack_client = get_slack_client(team_id)

        user_dm_channel_id = get_slack_user_dm_channel_id(slack_client, user_id)
        slack_client.chat_postMessage(
            channel=user_dm_channel_id,
            text='Looks like something went wrong :zipper_mouth_face: \n Please try again'
        )
        return JsonResponse({}, status=200)


    # Handle all the block actions from slack
    def handle_block_actions(self, slack_payload: Dict, user_id: str, team_id: str) -> Callable:
        '''
            Check if any function is associated with the action
            If present handler will call the respective function
            If not present call `handle_invalid_block_actions` to send a prompt to user
        '''

        # Initialize handlers
        self._initialize_block_action_handlers()

        action_id = slack_payload['actions'][0]['action_id']

        handler = self._block_action_handlers.get(action_id, self._handle_invalid_block_actions)

        return handler(slack_payload, user_id, team_id)


    # Define all the action handlers below this

    def handle_pre_auth_mock_button(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        # Empty function because slack still sends an interactive event on button click and expects a 200 response
        return JsonResponse({}, status=200)

    def link_fyle_account(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        # Empty function because slack still sends an interactive event on button click and expects a 200 response
        return JsonResponse({}, status=200)


    def review_report_in_fyle(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:

        report_id = slack_payload['actions'][0]['value']

        self.track_view_in_fyle_action(user_id, 'Report Viewed in Fyle', {'report_id': report_id})

        return JsonResponse({}, status=200)


    def expense_view_in_fyle(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:

        expense_id = slack_payload['actions'][0]['value']

        self.track_view_in_fyle_action(user_id, 'Expense Viewed in Fyle', {'expense_id': expense_id})

        return JsonResponse({}, status=200)


    def approve_report(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        report_id = slack_payload['actions'][0]['value']
        message_ts = slack_payload['message']['ts']
        message_blocks = slack_payload['message']['blocks']

        async_task(
            'fyle_slack_app.fyle.report_approvals.tasks.process_report_approval',
            report_id,
            user_id,
            team_id,
            message_ts,
            message_blocks
        )

        return JsonResponse({}, status=200)


    def handle_notification_preference_selection(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        user = utils.get_or_none(User, slack_user_id=user_id)
        assertions.assert_found(user)

        action_id = slack_payload['actions'][0]['action_id']
        value = slack_payload['actions'][0]['selected_option']['value']

        ACTION_NOTIFICATION_PREFERENCE_MAPPING = {
            'report_submitted_notification_preference': NotificationType.REPORT_SUBMITTED.value,
            'report_partially_approved_notification_preference': NotificationType.REPORT_PARTIALLY_APPROVED.value,
            'report_payment_processing_notification_preference': NotificationType.REPORT_PAYMENT_PROCESSING.value,
            'report_approver_sendback_notification_preference': NotificationType.REPORT_APPROVER_SENDBACK.value,
            'report_paid_notification_preference': NotificationType.REPORT_PAID.value,
            'report_commented_notification_preference': NotificationType.REPORT_COMMENTED.value,
            'expense_commented_notification_preference': NotificationType.EXPENSE_COMMENTED.value
        }

        is_enabled = True if value == 'enable' else False

        notification_type = ACTION_NOTIFICATION_PREFERENCE_MAPPING[action_id]

        notification_preference = NotificationPreference.objects.get(slack_user_id=user_id, notification_type=notification_type)
        notification_preference.is_enabled = is_enabled
        notification_preference.save()

        return JsonResponse({}, status=200)


    def handle_project_select(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:

        project_id = slack_payload['actions'][0]['selected_option']['value']

        view_id = slack_payload['container']['view_id']

        user = utils.get_or_none(User, slack_user_id=user_id)

        current_view = expense_messages.expense_form_loading_modal()
        current_view['submit'] = {'type': 'plain_text', 'text': 'Add Expense', 'emoji': True}

        blocks = slack_payload['view']['blocks']

        # Adding loading info below project input element
        project_block_index = next((index for (index, d) in enumerate(blocks) if d['block_id'] == 'project_block'), None)

        project_loading_block = {
			'type': 'context',
            'block_id': 'project_loading_block',
			'elements': [
				{
					'type': 'mrkdwn',
					'text': 'Loading categories for this project'
				}
			]
		}

        blocks.insert(project_block_index + 1, project_loading_block)

        current_view['blocks'] = blocks

        slack_client = get_slack_client(team_id)

        slack_client.views_update(view_id=view_id, view=current_view)

        async_task(
            'fyle_slack_app.slack.interactives.tasks.handle_project_select',
            user,
            team_id,
            project_id,
            view_id,
            slack_payload
        )

        return JsonResponse({})


    def handle_category_select(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:

        category_id = slack_payload['actions'][0]['selected_option']['value']

        view_id = slack_payload['container']['view_id']

        user = utils.get_or_none(User, slack_user_id=user_id)

        current_view = expense_messages.expense_form_loading_modal()
        current_view['submit'] = {'type': 'plain_text', 'text': 'Add Expense', 'emoji': True}

        blocks = slack_payload['view']['blocks']

        # Adding loading info below category input element
        category_block_index = next((index for (index, d) in enumerate(blocks) if d['block_id'] == 'category_block'), None)

        category_loading_block = {
			'type': 'context',
            'block_id': 'category_loading_block',
			'elements': [
				{
					'type': 'mrkdwn',
					'text': 'Loading additional fields for this category if any'
				}
			]
		}

        blocks.insert(category_block_index + 1, category_loading_block)

        current_view['blocks'] = blocks

        slack_client = get_slack_client(team_id)

        slack_client.views_update(view_id=view_id, view=current_view)

        async_task(
            'fyle_slack_app.slack.interactives.tasks.handle_category_select',
            user,
            team_id,
            category_id,
            view_id,
            slack_payload
        )

        return JsonResponse({}, status=200)


    # def handle_currency_select(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
    #     selected_currency = slack_payload['actions'][0]['selected_option']['value']

    #     view_id = slack_payload['container']['view_id']

    #     user = utils.get_or_none(User, slack_user_id=user_id)

    #     fyle_profile = get_fyle_profile(user.fyle_refresh_token)

    #     home_currency = fyle_profile['org']['currency']

    #     is_home_currency_selected = True
    #     if home_currency != selected_currency:
    #         is_home_currency_selected = False

    #     fyle_expense = FyleExpense(user)

    #     default_expense_fields = fyle_expense.get_default_expense_fields()

    #     slack_client = get_slack_client(team_id)

    #     projects_query_params = {
    #         'offset': 0,
    #         'limit': '100',
    #         'order': 'created_at.desc',
    #         'is_enabled': 'eq.{}'.format(True)
    #     }

    #     projects = fyle_expense.get_projects(projects_query_params)

    #     expense_form = expense_messages.expense_dialog_form(expense_fields=default_expense_fields, projects=projects)

    #     if is_home_currency_selected is False:


    #     slack_client.views_update(view_id=view_id, view=expense_form)



    def track_view_in_fyle_action(self, user_id: str, event_name: str, event_data: Dict) -> None:

        user = utils.get_or_none(User, slack_user_id=user_id)
        assertions.assert_found(user, 'user not found')

        event_data['email'] = user.email
        event_data['asset'] = 'SLACK_APP'

        tracking.identify_user(user.email)
        tracking.track_event(user.email, event_name, event_data)
