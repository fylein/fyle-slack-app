from typing import Dict, List

from slack_sdk.web import WebClient
from fyle.platform import exceptions

from fyle_slack_app.slack import utils as slack_utils
from fyle_slack_app.models import Team, User, UserFeedback
from fyle_slack_app.models.user_feedbacks import FeedbackTrigger
from fyle_slack_app.fyle.report_approvals.views import FyleReportApproval
from fyle_slack_app.libs import logger
from fyle_slack_app.fyle import utils as fyle_utils
from fyle_slack_app.libs import utils, assertions
from fyle_slack_app.slack.ui.notifications import messages as notification_messages


logger = logger.get_logger(__name__)


def process_report_approval(report_id: str, user_id: str, team_id: str, message_timestamp: str, notification_message: List[Dict]) -> Dict:

    slack_team = utils.get_or_none(Team, id=team_id)
    assertions.assert_found(slack_team, 'Slack team not registered')

    slack_client = WebClient(token=slack_team.bot_access_token)

    user = utils.get_or_none(User, slack_user_id=user_id)
    assertions.assert_found(user, 'Approver not found')

    fyle_report_approval = FyleReportApproval(user)

    try:
        report = fyle_report_approval.get_report_by_id(report_id)
    except exceptions.NotFoundItemError as error:
        logger.error('Report not found with id -> %s', report_id)
        logger.error('Error -> %s', error)
        # None here means report is deleted/doesn't exist
        report = None

    # Check if report is deleted
    if report is None:
        # Removing CTAs from notification message for deleted report
        report_notification_message = []
        for message_block in notification_message:
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
    else:
        report = report['data']
        can_approve_report, report_message = fyle_report_approval.can_approve_report(
            report,
            user.fyle_user_id
        )

        user_display_name = slack_utils.get_user_display_name(slack_client, report['user'])

        report_url = fyle_utils.get_fyle_resource_url(user.fyle_refresh_token, report, 'REPORT')

        if can_approve_report is True:
            try:
                report = fyle_report_approval.approve_report(report_id)
                report = report['data']
                report_message = 'Expense report approved :rocket:'

                # Track report approved
                fyle_report_approval.track_report_approved(user, report)

                # Trigger feedback
                UserFeedback.trigger_feedback(user, FeedbackTrigger.REPORT_APPROVED_FROM_SLACK, slack_client)

            except exceptions.PlatformError as error:
                logger.error('Error while processing report approve -> %s', error)

                message = 'Seems like an error occured while approving this report :face_with_head_bandage: \n' \
                    'Please try approving again or `Review in Fyle` to approve directly from Fyle :zap:'

                # Sending an error message in thread of notification message
                # With this CTAs are visible if approver wants to approve again
                slack_client.chat_postMessage(
                    channel=user.slack_dm_channel_id,
                    text=message,
                    thread_ts=message_timestamp
                )
                return None

        report_notification_message, title_text = notification_messages.get_report_approval_notification(
            report,
            user_display_name,
            report_url,
            report_message
        )

    slack_client.chat_update(
        text=title_text,
        channel=user.slack_dm_channel_id,
        blocks=report_notification_message,
        ts=message_timestamp
    )
