from typing import Dict

from fyle_slack_app.fyle.report_approvals.views import FyleReportApproval

from fyle_slack_app.models import User, UserFeedbackResponse
from fyle_slack_app.slack import utils as slack_utils
from fyle_slack_app.slack.ui.feedbacks import messages as feedback_messages
from fyle_slack_app.slack.ui.modals import messages as modal_messages
from fyle_slack_app import tracking

from fyle_slack_app.libs import utils, assertions, logger
logger = logger.get_logger(__name__)

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
        user=user,
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
        'comment': comment,
        'rating': rating,
        'email': user_email,
        'slack_user_id': user.slack_user_id
    }

    tracking.identify_user(user_email)
    tracking.track_event(user_email, 'Feedback Submitted', event_data)


def handle_fetch_report_expenses(user: User, slack_user_id: str, team_id: str, report: dict, modal_view_id: str):
    slack_client = slack_utils.get_slack_client(team_id)

    fyle_report_approval = FyleReportApproval(user)
    query_params = {
        'report_id': 'eq.{}'.format(report['id']),
        'order': 'created_at.desc',
        'limit': '20',
        'offset': '0'
    }

    try:
        approver_report_expenses = fyle_report_approval.get_approver_report_expenses(query_params=query_params)
        report_expenses = approver_report_expenses['data']
    except exceptions.NotFoundItemError as error:
        logger.error('Report expenses not found with id -> %s', report['id'])
        logger.error('Error -> %s', error)
        # None here means report is deleted/doesn't exist
        report_expenses = None

    report_expenses_dialog = modal_messages.get_report_expenses_dialog(user=user, report=report, report_expenses=report_expenses)

    slack_client.views_update(user=slack_user_id, view=report_expenses_dialog, view_id=modal_view_id)