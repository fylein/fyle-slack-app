from typing import Callable, Dict

from django.http.response import JsonResponse

from django_q.tasks import async_task

from fyle_slack_app.models.users import User
from fyle_slack_app.slack import utils as slack_utils
from fyle_slack_app.slack.interactives.block_action_handlers import BlockActionHandler
from fyle_slack_app.libs import utils


class ViewSubmissionHandler:

    _view_submission_handlers: Dict = {}

    # Maps action_id with it's respective function
    def _initialize_view_submission_handlers(self):
        self._view_submission_handlers = {
            'feedback_submission': self.handle_feedback_submission,
            'report_approval_from_modal': self.handle_report_approval_from_modal
        }


    # Gets called when function with a callback id is not found
    def _handle_invalid_view_submission(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        slack_client = slack_utils.get_slack_client(team_id)

        user_dm_channel_id = slack_utils.get_slack_user_dm_channel_id(slack_client, user_id)
        slack_client.chat_postMessage(
            channel=user_dm_channel_id,
            text='Looks like something went wrong :zipper_mouth_face: \n Please try again'
        )
        return JsonResponse({}, status=200)


    # Handle all the view_submission from slack
    def handle_view_submission(self, slack_payload: Dict, user_id: str, team_id: str) -> Callable:
        '''
            Check if any function is associated with the action
            If present handler will call the respective function
            If not present call `handle_invalid_view_submission` to send a prompt to user
        '''

        # Initialize handlers
        self._initialize_view_submission_handlers()

        callback_id = slack_payload['view']['callback_id']

        handler = self._view_submission_handlers.get(callback_id, self._handle_invalid_view_submission)

        return handler(slack_payload, user_id, team_id)


    def handle_feedback_submission(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:

        user = utils.get_or_none(User, slack_user_id=user_id)

        form_values = slack_payload['view']['state']['values']
        encoded_private_metadata = slack_payload['view']['private_metadata']
        private_metadata = utils.decode_state(encoded_private_metadata)

        async_task(
            'fyle_slack_app.slack.interactives.tasks.handle_feedback_submission',
            user,
            team_id,
            form_values,
            private_metadata
        )

        return JsonResponse({})


    def handle_report_approval_from_modal(self, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        encoded_private_metadata = slack_payload['view']['private_metadata']
        private_metadata = utils.decode_state(encoded_private_metadata)

        # Modifying the slack payload in order to mimic the payload structure sent to "approve_report" function
        slack_payload['actions'] = [
            {
                'value': private_metadata['report_id']
            }
        ]

        slack_payload['message'] = {}
        slack_payload['message']['ts'] = private_metadata['notification_message_ts']
        slack_payload['message']['blocks'] = private_metadata['notification_message_blocks']
        
        BlockActionHandler.approve_report(self=None, slack_payload=slack_payload, user_id=user_id, team_id=team_id)

        return JsonResponse({})