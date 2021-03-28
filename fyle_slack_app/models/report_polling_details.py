from django.db import models

from fyle_slack_app.models.users import User


class ReportPollingDetail(models.Model):

    class Meta:
        db_table = 'report_polling_details'

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    last_successful_poll_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return '{} - {}'.format(self.user, self.last_successful_poll_at)
