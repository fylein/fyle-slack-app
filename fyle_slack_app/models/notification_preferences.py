import enum

from django.db import models

from fyle_slack_app.models.users import User

# Defining notification types in <resource>_<resource_action> format
# Similar to payload received in webhook to keep it consistent
class NotificationType(enum.Enum):

    # Report notification types
    REPORT_SUBMITTED = 'REPORT_SUBMITTED'
    REPORT_COMMENTED = 'REPORT_COMMENTED'
    REPORT_APPROVED = 'REPORT_APPROVED'
    REPORT_PARTIALLY_APPROVED = 'REPORT_PARTIALLY_APPROVED'
    REPORT_APPROVER_SENDBACK = 'REPORT_APPROVER_SENDBACK'
    REPORT_PAYMENT_PROCESSING = 'REPORT_PAYMENT_PROCESSING'

    # Expense notification types
    EXPENSE_COMMENTED = 'EXPENSE_COMMENTED'


class NotificationPreference(models.Model):

    class Meta:
        db_table = 'notification_preferences'
        unique_together = ['slack_user', 'notification_type']

    slack_user = models.ForeignKey(User, on_delete=models.CASCADE, to_field='slack_user_id')
    notification_type = models.CharField(max_length=120)
    is_enabled = models.BooleanField(default=True)

    def __str__(self) -> str:
        return "{} - {}".format(self.slack_user.id, self.notification_type)
