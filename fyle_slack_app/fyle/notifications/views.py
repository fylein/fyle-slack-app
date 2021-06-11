from typing import Dict

import json

from django.http.request import HttpRequest
from django.http.response import JsonResponse
from django.views import View

from fyle_slack_app.libs import utils, assertions
from fyle_slack_app.slack import utils as slack_utils
from fyle_slack_app.fyle import utils as fyle_utils
from fyle_slack_app.models import User, NotificationPreference, UserSubscriptionDetail
from fyle_slack_app.models.notification_preferences import NotificationType
from fyle_slack_app.fyle.report_approvals.views import FyleReportApproval
from fyle_slack_app.slack.ui.notifications import messages as notification_messages


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

        self._initialize_event_handlers()

        handler = self.event_handlers.get(event_type)

        if handler is not None:

            user_subscription_detail = utils.get_or_none(UserSubscriptionDetail, webhook_id=webhook_id)
            assertions.assert_found(user_subscription_detail, 'User subscription not found with webhook id: {}'.format(webhook_id))

            slack_user_id = user_subscription_detail.slack_user_id

            user_notification_preference = NotificationPreference.objects.get(slack_user_id=slack_user_id, notification_type=event_type)

            if user_notification_preference.is_enabled is True:

                user = User.objects.get(slack_user_id=slack_user_id)

                return handler(webhook_data['data'], user)

        return JsonResponse({}, status=200)



class FyleFylerNotification(FyleNotificationView):

    def _initialize_event_handlers(self) -> None:
        self.event_handlers = {
            NotificationType.REPORT_PARTIALLY_APPROVED.value: self.handle_report_partially_approved,
            NotificationType.REPORT_PAYMENT_PROCESSING.value: self.handle_report_payment_processing,
            NotificationType.REPORT_APPROVER_SENDBACK.value: self.handle_report_approver_sendback,
            NotificationType.REPORT_SUBMITTED.value: self.handle_report_submitted
        }


    def handle_report_partially_approved(self, report: Dict, user: User) -> JsonResponse:

        slack_client = slack_utils.get_slack_client(user.slack_team_id)

        report_url = fyle_utils.get_fyle_report_url(user.fyle_refresh_token)

        report_notification_message = notification_messages.get_report_approved_notification(
            report,
            report_url
        )

        slack_client.chat_postMessage(
            channel=user.slack_dm_channel_id,
            blocks=report_notification_message
        )

        return JsonResponse({}, status=200)


    def handle_report_payment_processing(self, report: Dict, user: User) -> JsonResponse:

        slack_client = slack_utils.get_slack_client(user.slack_team_id)

        report_url = fyle_utils.get_fyle_report_url(user.fyle_refresh_token)

        report_notification_message = notification_messages.get_report_payment_processing_notification(
            report,
            report_url
        )

        slack_client.chat_postMessage(
            channel=user.slack_dm_channel_id,
            blocks=report_notification_message
        )

        return JsonResponse({}, status=200)


    def handle_report_approver_sendback(self, report: Dict, user: User) -> JsonResponse:

        slack_client = slack_utils.get_slack_client(user.slack_team_id)

        report_url = fyle_utils.get_fyle_report_url(user.fyle_refresh_token)

        report_notification_message = notification_messages.get_report_approver_sendback_notification(
            report,
            report_url
        )

        slack_client.chat_postMessage(
            channel=user.slack_dm_channel_id,
            blocks=report_notification_message
        )

        return JsonResponse({}, status=200)


    def handle_report_submitted(self, report: Dict, user: User) -> JsonResponse:

        slack_client = slack_utils.get_slack_client(user.slack_team_id)

        report_url = fyle_utils.get_fyle_report_url(user.fyle_refresh_token)

        report_notification_message = notification_messages.get_report_submitted_notification(
            report,
            report_url
        )

        slack_client.chat_postMessage(
            channel=user.slack_dm_channel_id,
            blocks=report_notification_message
        )

        return JsonResponse({}, status=200)


class FyleApproverNotification(FyleNotificationView):

    def _initialize_event_handlers(self) -> None:
        self.event_handlers = {
            NotificationType.REPORT_SUBMITTED.value: self.handle_report_submitted
        }


    def handle_report_submitted(self, report: Dict, user: User) -> JsonResponse:

        if report['state'] == 'APPROVER_PENDING':

            slack_client = slack_utils.get_slack_client(user.slack_team_id)

            report_url = fyle_utils.get_fyle_report_url(user.fyle_refresh_token)

            user_display_name = slack_utils.get_user_display_name(
                slack_client,
                report['user']
            )

            report_notification_message = notification_messages.get_report_approval_notification(
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

        return JsonResponse({}, status=200)
