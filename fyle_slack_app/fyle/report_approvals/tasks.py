from typing import Dict, List

from django.utils import timezone

from slack_sdk.web import WebClient
from fyle.platform import exceptions

from fyle_slack_app.slack import utils as slack_utils
from fyle_slack_app.models import ReportPollingDetail, Team, User, NotificationPreference
from fyle_slack_app.models.notification_preferences import NotificationType
from fyle_slack_app.fyle.report_approvals.views import FyleReportApproval
from fyle_slack_app.libs import logger
from fyle_slack_app.fyle import utils as fyle_utils
from fyle_slack_app.libs import utils, assertions
from fyle_slack_app.slack.ui.report_approvals import messages as report_approval_messages


logger = logger.get_logger(__name__)


def poll_report_approvals() -> None:
    polling_start_time = timezone.now()
    logger.info('Report polling started %s', polling_start_time)

    # Fetching only those users who have enabled report approval notifications
    report_approval_notification_preferences = NotificationPreference.objects.select_related('slack_user').filter(
        notification_type=NotificationType.APPROVER_REPORT_APPROVAL.value,
        is_enabled=True
    )

    for user_notification_preference in report_approval_notification_preferences:
        user = user_notification_preference.slack_user

        try:
            fyle_profile = fyle_utils.get_fyle_profile(user.fyle_refresh_token)
        except exceptions.NotFoundItemError as error:
            logger.info('Fyle profile not found for user %s - %s', user.slack_user_id, user.fyle_user_id)
            logger.info('API call error %s', error)

            return None

        if 'APPROVER' in fyle_profile['roles']:

            # select_related joins the two table with foreign key column
            # 1st join -> `report_polling_details` table with `users` table with `user` field
            # 2nd join -> `__slack_team` joins `users` table with `teams` table

            # 2 joins because we need user details (from `users` table) and team details (from `teams` table)
            report_polling_detail = ReportPollingDetail.objects.select_related('slack_user__slack_team').get(slack_user_id=user.slack_user_id)

            user = report_polling_detail.slack_user

            slack_client = WebClient(token=user.slack_team.bot_access_token)

            approver_user_id = user.fyle_user_id

            last_submitted_at = report_polling_detail.last_successful_poll_at.isoformat()

            # Fetch approver reports to approve - i.e. report state -> APPROVER_PENDING & approval state -> APPROVAL_PENDING
            query_params = {
                'state': 'eq.APPROVER_PENDING',
                'approvals': 'cs.[{{ "approver_user_id": {}, "state": "APPROVAL_PENDING" }}]'.format(approver_user_id),
                'last_submitted_at': 'gte.{}'.format(last_submitted_at),

                # Mandatory query params required by sdk
                'limit': 50, # Assuming no more than 50 reports will be there in 10 min poll
                'offset': 0,
                'order': 'last_submitted_at.desc'
            }

            approver_reports = FyleReportApproval.get_approver_reports(user, query_params)

            report_url = fyle_utils.get_fyle_report_url(user.fyle_refresh_token)

            if approver_reports['count'] > 0:
                # Save current timestamp as last_successful_poll_at
                # This will fetch new reports in next poll
                report_polling_detail.last_successful_poll_at = timezone.now()
                report_polling_detail.save()

                for report in approver_reports['data']:

                    user_display_name = slack_utils.get_user_display_name(
                        slack_client,
                        report['user']
                    )

                    report_notification_message = report_approval_messages.get_report_approval_notification(
                        report,
                        user_display_name,
                        report_url
                    )

                    slack_client.chat_postMessage(
                        channel=user.slack_dm_channel_id,
                        blocks=report_notification_message
                    )

                    # Track report approval notification received
                    FyleReportApproval.track_report_notification_received(user, report)

    polling_end_time = timezone.now()
    logger.info('Report polling ended %s', polling_end_time)
    logger.info('Polling time taken: %s', polling_end_time - polling_start_time)


def process_report_approval(report_id: str, user_id: str, team_id: str, message_timestamp: str, notification_message: List[Dict]) -> Dict:

    slack_team = utils.get_or_none(Team, id=team_id)
    assertions.assert_found(slack_team, 'Slack team not registered')

    slack_client = WebClient(token=slack_team.bot_access_token)

    user = utils.get_or_none(User, slack_user_id=user_id)
    assertions.assert_found(user, 'Approver not found')

    try:
        report = FyleReportApproval.get_report_by_id(user, report_id)
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
        report_notification_message = slack_utils.add_message_section_to_ui_block(
            report_notification_message,
            report_message
        )
    else:
        report = report['data']
        can_approve_report, report_message = FyleReportApproval.can_approve_report(
            report,
            user.fyle_user_id
        )

        user_display_name = slack_utils.get_user_display_name(slack_client, report['user'])

        report_url = fyle_utils.get_fyle_report_url(user.fyle_refresh_token)

        if can_approve_report is True:
            try:
                report = FyleReportApproval.approve_report(user, report_id)
                report = report['data']
                report_message = 'Expense report approved :rocket:'

                # Track report approved
                FyleReportApproval.track_report_approved(user, report)

            except exceptions.PlatformError as error:
                logger.error('Error while processing report approve -> %s', error)

                message = 'Seems like an error occured while approving this report :face_with_head_bandage: \n' \
                    'Please try approving again or `Review in Fyle` to approve directly from Fyle :zap:'

                # Sending an error message in thread of notification message
                # With this CTAs are visible if approver wants to approve again
                slack_client.chat_postMessage(
                    channel=user.slack_dm_channel_id,
                    message=message,
                    thread_ts=message_timestamp
                )
                return None

        report_notification_message = report_approval_messages.get_report_approval_notification(
            report,
            user_display_name,
            report_url,
            report_message
        )

    slack_client.chat_update(
        channel=user.slack_dm_channel_id,
        blocks=report_notification_message,
        ts=message_timestamp
    )
