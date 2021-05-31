from typing import Dict

import json

from django.http.request import HttpRequest
from django.http.response import JsonResponse
from django.views import View

from fyle_slack_app.libs import utils, assertions
from fyle_slack_app.slack import utils as slack_utils
from fyle_slack_app.fyle import utils as fyle_utils
from fyle_slack_app.models import User, NotificationPreference
from fyle_slack_app.models.notification_preferences import NotificationType
from fyle_slack_app.fyle.report_approvals.views import FyleReportApproval
from fyle_slack_app.slack.ui.notifications import messages as notification_messages



class FyleFylerNotification(View):

    event_handlers: Dict = {}

    def _initialize_event_handlers(self) -> None:
        self.event_handlers = {
            NotificationType.REPORT_PARTIALLY_APPROVED.value: self.handle_report_partially_approved
        }


    def handler_invalid_event(self, data: Dict) -> JsonResponse:
        return JsonResponse({}, status=200)


    def post(self, request: HttpRequest, user_id: str) -> JsonResponse:
        webhook_data = json.loads(request.body)

        # Construct event data in <resource>_<action> format
        event_type = '{}_{}'.format(webhook_data['resource'], webhook_data['action'])

        self._initialize_event_handlers()

        user = utils.get_or_none(User, fyle_user_id=user_id)
        assertions.assert_found(user, 'User not found for fyle user id: {}'.format(user_id))

        user_notification_preference = NotificationPreference.objects.get(slack_user_id=user.slack_user_id, notification_type=event_type)

        if user_notification_preference.is_enabled is True:

            handler = self.event_handlers.get(event_type, self.handler_invalid_event)

            return handler(webhook_data['data'], user)

        return JsonResponse({}, status=200)


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


class FyleApproverNotification(View):

    event_handlers: Dict = {}

    def _initialize_event_handlers(self) -> None:
        self.event_handlers = {
            NotificationType.REPORT_SUBMITTED.value: self.handle_report_submitted
        }


    def handler_invalid_event(self, data: Dict) -> JsonResponse:
        return JsonResponse({}, status=200)


    def post(self, request: HttpRequest, approver_user_id: str) -> JsonResponse:
        webhook_data = json.loads(request.body)

        # Construct event data in <resource>_<action> format
        event_type = '{}_{}'.format(webhook_data['resource'], webhook_data['action'])

        self._initialize_event_handlers()

        user = utils.get_or_none(User, fyle_user_id=approver_user_id)
        assertions.assert_found(user, 'User not found for fyle user id: {}'.format(approver_user_id))

        user_notification_preference = NotificationPreference.objects.get(slack_user_id=user.slack_user_id, notification_type=event_type)

        if user_notification_preference.is_enabled is True:

            handler = self.event_handlers.get(event_type, self.handler_invalid_event)

            return handler(webhook_data['data'], user)

        return JsonResponse({}, status=200)


    def handle_report_submitted(self, report: Dict, user: User) -> JsonResponse:

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
