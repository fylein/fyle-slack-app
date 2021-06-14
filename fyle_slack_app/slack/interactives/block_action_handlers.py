from typing import Callable, Dict

from django.http import JsonResponse

from django_q.tasks import async_task

from fyle.platform import exceptions

from fyle_slack_app.models import User, NotificationPreference
from fyle_slack_app.models.notification_preferences import NotificationType
from fyle_slack_app.libs import assertions, utils, logger
from fyle_slack_app.slack.utils import get_slack_user_dm_channel_id, get_slack_client
from fyle_slack_app.fyle.report_approvals.views import FyleReportApproval


logger = logger.get_logger(__name__)


class BlockActionHandler:

    _block_action_handlers: Dict = {}

    # Maps action_id with it's respective function
    def _initialize_block_action_handlers(self):
        self._block_action_handlers = {
            'link_fyle_account': self.link_fyle_account,
            'review_report_in_fyle': self.review_report_in_fyle,
            'approve_report': self.approve_report,
            'report_submitted_notification_preference': self.handle_notification_preference_selection,
            'report_partially_approved_notification_preference': self.handle_notification_preference_selection,
            'report_payment_processing_notification_preference': self.handle_notification_preference_selection,
            'report_approver_sendback_notification_preference': self.handle_notification_preference_selection
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

    def link_fyle_account(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        # Empty function because slack still sends an interactive event on button click and expects a 200 response
        return JsonResponse({}, status=200)


    def review_report_in_fyle(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        report_id = slack_payload['actions'][0]['value']
        message_timestamp = slack_payload['message']['ts']
        message_blocks = slack_payload['message']['blocks']

        user = utils.get_or_none(User, slack_user_id=user_id)
        assertions.assert_found(user)

        try:
            # pylint: disable=unused-variable
            report = FyleReportApproval.get_report_by_id(user, report_id)
        except exceptions.NotFoundItemError as error:
            logger.error('Error while fetching report of id: %s \n %s', report_id, error)

            # Removing CTAs from notification message for deleted report
            report_notification_message = []
            for message_block in message_blocks:
                if message_block['type'] != 'actions':
                    report_notification_message.append(message_block)

            report_message = 'Looks like you no longer have access to this expense report :face_with_head_bandage:'
            report_deleted_section = {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': report_message
                }
            }
            report_notification_message.insert(3, report_deleted_section)

            slack_client = get_slack_client(team_id)

            slack_client.chat_update(
                channel=user.slack_dm_channel_id,
                blocks=report_notification_message,
                ts=message_timestamp
            )

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
            'report_approver_sendback_notification_preference': NotificationType.REPORT_APPROVER_SENDBACK.value
        }

        is_enabled = True if value == 'enable' else False

        notification_type = ACTION_NOTIFICATION_PREFERENCE_MAPPING[action_id]

        notification_preference = NotificationPreference.objects.get(slack_user_id=user_id, notification_type=notification_type)
        notification_preference.is_enabled = is_enabled
        notification_preference.save()

        return JsonResponse({}, status=200)
