from typing import Dict

from fyle_slack_app.models import User, UserFeedbackResponse
from fyle_slack_app.slack import utils as slack_utils
from fyle_slack_app.slack.ui.feedbacks import messages as feedback_messages
from fyle_slack_app import tracking


def handle_feedback_submission(user: User, team_id: str, form_values: Dict, private_metadata: Dict):
    user_feedback_id = private_metadata['user_feedback_id']
    feedback_message_ts = private_metadata['feedback_message_ts']
    feedback_trigger = private_metadata['feedback_trigger']

    slack_client = slack_utils.get_slack_client(team_id)

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

    user_email = user.email
    event_data = {
        'feedback_trigger': feedback_trigger,
        'email': user_email,
        'slack_user_id': user.slack_user_id
    }

    tracking.identify_user(user_email)
    tracking.track_event(user_email, 'Feedback Submitted', event_data)
