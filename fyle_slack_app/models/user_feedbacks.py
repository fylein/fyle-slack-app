import enum

from django.db import models

from slack_sdk.web import WebClient

from fyle_slack_app.models.users import User
from fyle_slack_app.slack.ui.feedbacks import messages as feedback_messages


class FeedbackTrigger(enum.Enum):
    REPORT_APPROVED_FROM_SLACK = 'REPORT_APPROVED_FROM_SLACK'


class UserFeedback(models.Model):

    class Meta:
        db_table = 'user_feedbacks'

    feedback_trigger = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    last_feedback_shown_at = models.DateTimeField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return '{} - {}'.format(self.feedback_trigger, self.user.slack_user_id)


    @staticmethod
    def trigger_feedback(user: User, feedback_trigger: FeedbackTrigger, slack_client: WebClient):

        user_feedback, _ = UserFeedback.objects.get_or_create(
            feedback_trigger=feedback_trigger,
            user=user
        )

        if user_feedback.is_active:
            feedback_message = feedback_messages.get_user_feedback_message(user_feedback.id)
            slack_client.chat_postMessage(
                channel=user.slack_dm_channel_id,
                blocks=feedback_message
            )


class UserFeedbackResponse(models.Model):

    class Meta:
        db_table = 'user_feedback_responses'

    user_feedback = models.ForeignKey(UserFeedback, on_delete=models.SET_NULL, null=True)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return '{} - {}'.format(self.user_feedback.__str__, self.rating)
