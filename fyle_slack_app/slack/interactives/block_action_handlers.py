from typing import Callable, Dict

from django.http import JsonResponse

from django_q.tasks import async_task

from fyle_slack_app.models import User, NotificationPreference, UserFeedback
from fyle_slack_app.models.notification_preferences import NotificationType
from fyle_slack_app.libs import assertions, utils, logger
from fyle_slack_app.slack.utils import get_slack_client
from fyle_slack_app.slack.ui.feedbacks import messages as feedback_messages
from fyle_slack_app.slack import utils as slack_utils
from fyle_slack_app import tracking
from fyle_slack_app.slack.ui.common_messages import IN_PROGRESS_MESSAGE


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
            'open_feedback_dialog': self.handle_feedback_dialog,
            'sent_back_reports_viewed_in_fyle': self.handle_tasks_viewed_in_fyle,
            'incomplete_expenses_viewed_in_fyle': self.handle_tasks_viewed_in_fyle,
            'unreported_expenses_viewed_in_fyle': self.handle_tasks_viewed_in_fyle,
            'draft_reports_viewed_in_fyle': self.handle_tasks_viewed_in_fyle
        }


    # Gets called when function with an action is not found
    def _handle_invalid_block_actions(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        slack_client = slack_utils.get_slack_client(team_id)

        user_dm_channel_id = slack_utils.get_slack_user_dm_channel_id(slack_client, user_id)
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

        # Overriding the 'approve' cta text to 'approving'
        in_progress_message_block = IN_PROGRESS_MESSAGE[slack_utils.AsyncOperation.APPROVING_REPORT.value]
        message_blocks[3]['elements'][0] = in_progress_message_block

        slack_client = slack_utils.get_slack_client(team_id)
        user_dm_channel_id = slack_utils.get_slack_user_dm_channel_id(slack_client, user_id)
        slack_client.chat_update(
            channel=user_dm_channel_id,
            blocks=message_blocks,
            ts=message_ts
        )

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


    def handle_feedback_dialog(self, slack_payload: Dict, user_id: str, team_id: str) -> None:

        slack_client = get_slack_client(team_id)

        message_ts = slack_payload['message']['ts']
        trigger_id = slack_payload['trigger_id']
        feedback_trigger = slack_payload['actions'][0]['value']

        user_feedback = utils.get_or_none(UserFeedback, user_id=user_id, feedback_trigger=feedback_trigger)

        private_metadata = {
            'user_feedback_id': user_feedback.id,
            'feedback_message_ts': message_ts,
            'feedback_trigger': feedback_trigger
        }
        encoded_private_metadata = utils.encode_state(private_metadata)

        feedback_dialog = feedback_messages.get_feedback_dialog(private_metadata=encoded_private_metadata)

        # Since they've opened up the model we'll set is_active to False so that the feedback message won't be shown again
        UserFeedback.update_feedback_active_and_feedback_shown_time(
           user_feedback=user_feedback
        )

        slack_client.views_open(user=user_id, view=feedback_dialog, trigger_id=trigger_id)

        user_email = user_feedback.user.email
        event_data = {
            'feedback_trigger': feedback_trigger,
            'email': user_email,
            'slack_user_id': user_id
        }

        tracking.identify_user(user_email)
        tracking.track_event(user_email, 'Feedback Modal Opened', event_data)

        return JsonResponse({})


    def handle_tasks_viewed_in_fyle(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        user = utils.get_or_none(User, slack_user_id=user_id)
        task_name = slack_payload['actions'][0]['value']
        event_data = {
            'slack_user_id': user_id,
            'team_id': team_id,
            'task': task_name,
            'email': user.email,
            'fyle_org_id': user.fyle_org_id,
            'fyle_user_id': user.fyle_user_id
        }
        self.track_view_in_fyle_action(user_id, task_name, event_data)

        return JsonResponse({})


    def track_view_in_fyle_action(self, user_id: str, event_name: str, event_data: Dict) -> None:

        user = utils.get_or_none(User, slack_user_id=user_id)
        assertions.assert_found(user, 'user not found')

        event_data['email'] = user.email
        event_data['asset'] = 'SLACK_APP'

        tracking.identify_user(user.email)
        tracking.track_event(user.email, event_name, event_data)
