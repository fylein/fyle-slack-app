import enum

from django.utils import timezone
from django.db import models

from slack_sdk.web import WebClient
from fyle_slack_app.libs import utils

from fyle_slack_app.models.users import User
from fyle_slack_app.slack.ui.feedbacks import messages as feedback_messages
from fyle_slack_app import tracking


class FeedbackTrigger(enum.Enum):
    REPORT_APPROVED_FROM_SLACK = 'REPORT_APPROVED_FROM_SLACK'


class UserFeedback(models.Model):

    class Meta:
        db_table = 'user_feedbacks'

    id = models.CharField(max_length=120, unique=True, primary_key=True)
    feedback_trigger = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, to_field='slack_user_id', null=True)
    is_active = models.BooleanField(default=False)
    last_feedback_shown_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return '{} - {}'.format(self.feedback_trigger, self.user.slack_user_id)


    @staticmethod
    def get_or_create(user: User, feedback_trigger: FeedbackTrigger):
        is_created = False
        user_feedback = utils.get_or_none(UserFeedback, feedback_trigger=feedback_trigger.value, user=user)

        if user_feedback is None:
            user_feedback = UserFeedback.objects.create(
                id='uf{}'.format(utils.generate_random_string()),
                feedback_trigger=feedback_trigger.value,
                user=user
            )
            is_created = True

        return user_feedback, is_created


    @staticmethod
    def trigger_feedback(user: User, feedback_trigger: FeedbackTrigger, slack_client: WebClient):

        user_feedback, is_created = UserFeedback.get_or_create(
            feedback_trigger=feedback_trigger,
            user=user
        )

        if user_feedback.is_active or is_created is True:
            feedback_message = feedback_messages.get_user_feedback_message(feedback_trigger.value)

            slack_client.chat_postMessage(
                channel=user.slack_dm_channel_id,
                blocks=feedback_message
            )
            user_email = user.email
            event_data = {
                'feedback_trigger': feedback_trigger,
                'email': user_email,
                'slack_user_id': user.slack_user_id
            }

            tracking.identify_user(user_email)
            tracking.track_event(user_email, 'Feedback Message Received', event_data)


    @staticmethod
    def update_feedback_active_and_feedback_shown_time(user_feedback):
        user_feedback.last_feedback_shown_at = timezone.now()
        user_feedback.is_active = False
        user_feedback.save()


class UserFeedbackResponse(models.Model):

    class Meta:
        db_table = 'user_feedback_responses'

    user_feedback = models.ForeignKey(UserFeedback, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, to_field='slack_user_id', null=True, unique=False)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return '{} - {}'.format(self.user_feedback.__str__, self.rating)


    @staticmethod
    def create_user_feedback_response(user_feedback_id: int, rating: int, comment: str, user: User):
        user_feedback = utils.get_or_none(UserFeedback, id=user_feedback_id)

        user_feedback_response = UserFeedbackResponse.objects.create(
            user_feedback=user_feedback,
            user=user,
            rating=rating,
            comment=comment
        )

        return user_feedback_response
