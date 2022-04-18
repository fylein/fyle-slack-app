from typing import Dict

import json

from django.http.request import HttpRequest
from django.http.response import JsonResponse
from django.views import View

from slack_sdk.web.client import WebClient

from fyle_slack_app import tracking
from fyle_slack_app.libs import utils, assertions, logger
from fyle_slack_app.fyle import utils as fyle_utils
from fyle_slack_app.fyle.corporate_cards.views import FyleCorporateCard
from fyle_slack_app.slack import utils as slack_utils
from fyle_slack_app.slack.ui.notifications import messages as notification_messages
from fyle_slack_app.models import User, NotificationPreference, UserSubscriptionDetail
from fyle_slack_app.models.notification_preferences import NotificationType

logger = logger.get_logger(__name__)


class FyleNotificationView(View):

    event_handlers: Dict = {}

    def post(self, request: HttpRequest, webhook_id: str) -> JsonResponse:
        webhook_data = json.loads(request.body)

        resource = webhook_data['resource']
        action = webhook_data['action']

        # pylint: disable=fixme
        # TODO: Below might not be a good way defining event_type
        # Try to find a better way if possible

        # Constructing event in `<resource>_<action>` format
        # This is equivalent to the notification types defined
        event_type = '{}_{}'.format(resource, action)

        logger.info('Notification type received -> %s', event_type)

        self._initialize_event_handlers()

        handler = self.event_handlers.get(event_type)

        if handler is not None:

            user_subscription_detail = utils.get_or_none(UserSubscriptionDetail, webhook_id=webhook_id)
            assertions.assert_found(user_subscription_detail, 'User subscription not found with webhook id: {}'.format(webhook_id))

            slack_user_id = user_subscription_detail.slack_user_id

            user_notification_preference = NotificationPreference.objects.get(slack_user_id=slack_user_id, notification_type=event_type)

            if user_notification_preference.is_enabled is True:

                user = User.objects.get(slack_user_id=slack_user_id)

                slack_client = slack_utils.get_slack_client(user.slack_team_id)

                return handler(webhook_data, user, slack_client)

        return JsonResponse({}, status=200)


    @staticmethod
    def get_event_data(user: User) -> Dict:
        event_data = {
            'asset': 'SLACK_APP',
            'slack_user_id': user.slack_user_id,
            'fyle_user_id': user.fyle_user_id,
            'email': user.email,
            'slack_team_id': user.slack_team.id,
            'slack_team_name': user.slack_team.name,
        }
        return event_data


    @staticmethod
    def get_report_tracking_data(user: User, report: Dict) -> Dict:
        event_data = FyleNotificationView.get_event_data(user)

        event_data['report_id'] = report['id']
        event_data['org_id'] = report['org_id']

        return event_data


    @staticmethod
    def get_expense_tracking_data(user: User, expense: Dict) -> Dict:
        event_data = FyleNotificationView.get_event_data(user)

        event_data['expense_id'] = expense['id']
        event_data['org_id'] = expense['org_id']

        return event_data


    @staticmethod
    def track_notification(event_name: str, user: User, resource_type: str, resource: Dict) -> None:

        if resource_type == 'REPORT':
            event_data = FyleNotificationView.get_report_tracking_data(user, resource)
        elif resource_type == 'EXPENSE':
            event_data = FyleNotificationView.get_expense_tracking_data(user, resource)

        tracking.identify_user(user.email)

        tracking.track_event(user.email, event_name, event_data)


class FyleFylerNotification(FyleNotificationView):

    def _initialize_event_handlers(self) -> None:
        self.event_handlers = {
            NotificationType.REPORT_PARTIALLY_APPROVED.value: self.handle_report_partially_approved,
            NotificationType.REPORT_PAYMENT_PROCESSING.value: self.handle_report_payment_processing,
            NotificationType.REPORT_SUBMITTED.value: self.handle_report_submitted,
            NotificationType.REPORT_APPROVER_SENDBACK.value: self.handle_report_approver_sendback,
            NotificationType.REPORT_COMMENTED.value: self.handle_report_commented,
            NotificationType.EXPENSE_COMMENTED.value: self.handle_expense_commented,
            NotificationType.EXPENSE_MANDATORY_RECEIPT_MISSING.value: self.handle_expense_mandatory_receipt_missing,
            NotificationType.REPORT_PAID.value: self.handle_report_paid
        }


    def handle_report_partially_approved(self, webhook_data: Dict, user: User, slack_client: WebClient) -> JsonResponse:

        report = webhook_data['data']

        report_url = fyle_utils.get_fyle_resource_url(user.fyle_refresh_token, report, 'REPORT')

        report_notification_message, title_text = notification_messages.get_report_approved_notification(
            report,
            report_url
        )

        slack_client.chat_postMessage(
            text=title_text,
            channel=user.slack_dm_channel_id,
            blocks=report_notification_message
        )

        self.track_notification('Report Partially Approved Notification Received', user, 'REPORT', report)

        return JsonResponse({}, status=200)


    def handle_report_payment_processing(self, webhook_data: Dict, user: User, slack_client: WebClient) -> JsonResponse:

        report = webhook_data['data']

        report_url = fyle_utils.get_fyle_resource_url(user.fyle_refresh_token, report, 'REPORT')

        report_notification_message, title_text = notification_messages.get_report_payment_processing_notification(
            report,
            report_url
        )

        slack_client.chat_postMessage(
            text=title_text,
            channel=user.slack_dm_channel_id,
            blocks=report_notification_message
        )

        self.track_notification('Report Payment Processing Notification Received', user, 'REPORT', report)

        return JsonResponse({}, status=200)


    def handle_report_approver_sendback(self, webhook_data: Dict, user: User, slack_client: WebClient) -> JsonResponse:

        report = webhook_data['data']

        report_sendback_reason = webhook_data['reason']

        report_url = fyle_utils.get_fyle_resource_url(user.fyle_refresh_token, report, 'REPORT')

        report_notification_message, title_text = notification_messages.get_report_approver_sendback_notification(
            report,
            report_url,
            report_sendback_reason
        )

        slack_client.chat_postMessage(
            text=title_text,
            channel=user.slack_dm_channel_id,
            blocks=report_notification_message
        )

        self.track_notification('Report Approver Sendback Notification Received', user, 'REPORT', report)

        return JsonResponse({}, status=200)


    def handle_report_submitted(self, webhook_data: Dict, user: User, slack_client: WebClient) -> JsonResponse:

        report = webhook_data['data']

        report_url = fyle_utils.get_fyle_resource_url(user.fyle_refresh_token, report, 'REPORT')

        report_notification_message, title_text = notification_messages.get_report_submitted_notification(
            report,
            report_url
        )

        slack_client.chat_postMessage(
            text=title_text,
            channel=user.slack_dm_channel_id,
            blocks=report_notification_message
        )

        self.track_notification('Report Submitted Notification Received', user, 'REPORT', report)

        return JsonResponse({}, status=200)


    def handle_report_commented(self, webhook_data: Dict, user: User, slack_client: WebClient) -> JsonResponse:

        report = webhook_data['data']

        # Send comment notification only if the commenter is not SYSTEM and not the user itself
        if report['updated_by_user']['id'] not in ['SYSTEM', report['user']['id']]:

            report_url = fyle_utils.get_fyle_resource_url(user.fyle_refresh_token, report, 'REPORT')

            report_comment = webhook_data['reason']

            user_display_name = slack_utils.get_user_display_name(
                slack_client,
                report['updated_by_user']
            )

            report_notification_message, title_text = notification_messages.get_report_commented_notification(report, user_display_name, report_url, report_comment)

            slack_client.chat_postMessage(
                text=title_text,
                channel=user.slack_dm_channel_id,
                blocks=report_notification_message
            )

            self.track_notification('Report Commented Notification Received', user, 'REPORT', report)

        return JsonResponse({}, status=200)


    def handle_expense_commented(self, webhook_data: Dict, user: User, slack_client: WebClient) -> JsonResponse:

        expense = webhook_data['data']

        # Send comment notification only if the commenter is not SYSTEM and not the user itself
        if expense['updated_by_user']['id'] not in ['SYSTEM', expense['employee']['user']['id']]:

            expense_url = fyle_utils.get_fyle_resource_url(user.fyle_refresh_token, expense, 'EXPENSE')

            expense_comment = webhook_data['reason']

            user_display_name = slack_utils.get_user_display_name(
                slack_client,
                expense['updated_by_user']
            )

            expense_notification_message, title_text = notification_messages.get_expense_commented_notification(expense, user_display_name, expense_url, expense_comment)

            slack_client.chat_postMessage(
                text=title_text,
                channel=user.slack_dm_channel_id,
                blocks=expense_notification_message
            )

            self.track_notification('Expense Commented Notification Received', user, 'EXPENSE', expense)

        return JsonResponse({}, status=200)


    def handle_expense_mandatory_receipt_missing(self, webhook_data: Dict, user: User, slack_client: WebClient) -> JsonResponse:
        expense = webhook_data['data']

        # Check if there are any matched corporate_card_transactions
        if expense['matched_corporate_card_transactions'] is not None and len(expense['matched_corporate_card_transactions']) > 0:

            corporate_card_id = expense['matched_corporate_card_transactions'][0]['corporate_card_id']

            # Fetch corporate card
            card = FyleCorporateCard(user).get_corporate_card_by_id(corporate_card_id)

            if card['count'] > 0 and card['data'][0]['is_visa_enrolled'] is True:
                expense_url = fyle_utils.get_fyle_resource_url(user.fyle_refresh_token, expense, 'EXPENSE')

                card_expense_notification_message, title_text = notification_messages.get_expense_mandatory_receipt_missing_notification(
                    expense,
                    expense_url
                )

                slack_client.chat_postMessage(
                    text=title_text,
                    channel=user.slack_dm_channel_id,
                    blocks=card_expense_notification_message
                )

                self.track_notification('Visa Card Expense Notification Received', user, 'EXPENSE', expense)

        return JsonResponse({}, status=200)


    def handle_report_paid(self, webhook_data: Dict, user: User, slack_client: WebClient) -> JsonResponse:

        report = webhook_data['data']

        report_url = fyle_utils.get_fyle_resource_url(user.fyle_refresh_token, report, 'REPORT')

        report_notification_message, title_text = notification_messages.get_report_paid_notification(
            report,
            report_url
        )

        slack_client.chat_postMessage(
            text=title_text,
            channel=user.slack_dm_channel_id,
            blocks=report_notification_message
        )

        self.track_notification('Report Paid Notification Received', user, 'REPORT', report)

        return JsonResponse({}, status=200)


class FyleApproverNotification(FyleNotificationView):

    def _initialize_event_handlers(self) -> None:
        self.event_handlers = {
            NotificationType.REPORT_SUBMITTED.value: self.handle_report_submitted
        }


    def handle_report_submitted(self, webhook_data: Dict, user: User, slack_client: WebClient) -> JsonResponse:

        report = webhook_data['data']

        if report['state'] == 'APPROVER_PENDING':

            report_url = fyle_utils.get_fyle_resource_url(user.fyle_refresh_token, report, 'REPORT')

            user_display_name = slack_utils.get_user_display_name(
                slack_client,
                report['user']
            )

            report_notification_message, title_text = notification_messages.get_report_approval_notification(
                report,
                user_display_name,
                report_url
            )

            slack_client.chat_postMessage(
                text=title_text,
                channel=user.slack_dm_channel_id,
                blocks=report_notification_message
            )

            self.track_notification('Report Approval Notification Received', user, 'REPORT', report)

        return JsonResponse({}, status=200)
