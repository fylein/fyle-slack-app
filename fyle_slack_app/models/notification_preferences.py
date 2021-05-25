import enum

from django.db import models

from fyle_slack_app.models.users import User

# Defining notification types in <role>_<event_type>
class NotificationType(enum.Enum):
    APPROVER_REPORT_APPROVAL = 'APPROVER_REPORT_APPROVAL'


class NotificationPreference(models.Model):

    class Meta:
        db_table = 'notification_preferences'
        unique_together = ['slack_user', 'notification_type']

    slack_user = models.ForeignKey(User, on_delete=models.CASCADE, to_field='slack_user_id')
    notification_type = models.CharField(max_length=120)
    is_enabled = models.BooleanField(default=True)

    def __str__(self) -> str:
        return "{} - {}".format(self.slack_user.id, self.notification_type)
