import enum

from django.db import models

from fyle_slack_app.models.users import User


class SubscriptionType(enum.Enum):
    FYLER_SUBSCRIPTION = 'FYLER_SUBSCRIPTION'
    APPROVER_SUBSCRIPTION = 'APPROVER_SUBSCRIPTION'


class UserSubscriptionDetail(models.Model):
    class Meta:
        db_table = 'user_subscription_details'
        unique_together = ['slack_user', 'subscription_type']

    slack_user = models.ForeignKey(User, on_delete=models.CASCADE, to_field='slack_user_id')
    subscription_type = models.CharField(max_length=120)
    subscription_id = models.CharField(max_length=120, unique=True)


    def __str__(self) -> str:
        return '{} - {}'.format(self.slack_user.id, self.subscription_type)
