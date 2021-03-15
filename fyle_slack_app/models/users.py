from django.db import models

from .teams import Team

class User(models.Model):

    class Meta:
        db_table = 'users'

    slack_user_id = models.CharField(max_length=120, primary_key=True)
    slack_team = models.ForeignKey(Team, on_delete=models.CASCADE)
    slack_dm_channel_id = models.CharField(max_length=120, unique=True)
    email = models.EmailField()
    fyle_refresh_token = models.TextField()
    fyle_employee_id = models.CharField(max_length=120, null=True) # null=True because this column was added later and django migration needs a default value to fill existing rows
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} - {}".format(self.slack_user_id, self.email)
