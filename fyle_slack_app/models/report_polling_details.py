from django.db import models

from .users import User


class ReportPollingDetail(models.Model):

    class Meta:
        db_table = 'report_polling_details'

    slack_user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True, to_field='slack_user_id')
    last_successful_poll_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} - {}'.format(self.slack_user, self.last_successful_poll_at)
