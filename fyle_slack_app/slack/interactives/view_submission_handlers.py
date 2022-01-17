from typing import Callable, Dict

from django.http.response import JsonResponse

from fyle_slack_app.models import UserFeedbackResponse
from fyle_slack_app.models.users import User
from fyle_slack_app.slack import utils as slack_utils
from fyle_slack_app.libs import utils
from fyle_slack_app.slack.ui.feedbacks import messages as feedback_messages



class ViewSubmissionHandler:

    _view_submission_handlers: Dict = {}

    # Maps action_id with it's respective function
    def _initialize_view_submission_handlers(self):
        self._view_submission_handlers = {
            'feedback_submission': self.handle_feedback_submission
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

        encoded_private_metadata = slack_payload['view']['private_metadata']

        private_metadata = utils.decode_state(encoded_private_metadata)

        user_feedback_id = private_metadata['user_feedback_id']
        feedback_message_ts = private_metadata['feedback_message_ts']

        slack_client = slack_utils.get_slack_client(team_id)

        form_values = slack_payload['view']['state']['values']

        rating = int(form_values['rating_block']['rating']['selected_option']['value'])
        comment = form_values['comment_block']['comment']['value']

        # Register user feedback response
        UserFeedbackResponse.create_user_feedback_response(
            user_feedback_id=user_feedback_id,
            rating=rating,
            comment=comment
        )

        post_feedback_submission_message = feedback_messages.get_post_feedback_submission_message()

        # Upadate original feedback message
        slack_client.chat_update(
            text='Thanks for submitting the feedback',
            blocks=post_feedback_submission_message,
            channel=user.slack_dm_channel_id,
            ts=feedback_message_ts
        )

        return JsonResponse({})
