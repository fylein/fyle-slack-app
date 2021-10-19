import enum

from django.db import models

from fyle_slack_app.models.users import User


class ExpenseFlowType(enum.Enum):
    EXPENSE_FORM = 'EXPENSE_FORM'
    RECEIPT_UPLOAD = 'RECEIPT_UPLOAD'


class ExpenseProcessingDetails(models.Model):

    class Meta:
        db_table = 'expense_processing_details'

    slack_user = models.ForeignKey(User, on_delete=models.CASCADE, to_field='slack_user_id')
    expense_details = models.JSONField(null=True, blank=True)
    slack_view_id = models.CharField(max_length=120, unique=True, null=True, blank=True)
    form_metadata = models.JSONField(null=True, blank=True)
    is_successfully_processed = models.BooleanField(default=False)
    expense_flow_type = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return '{} - {} - {}'.format(self.slack_user.slack_user_id, self.slack_view_id, self.is_successfully_processed)
