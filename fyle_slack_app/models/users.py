from django.db import models

from fyle_slack_app.models.teams import Team

class User(models.Model):

    class Meta:
        db_table = 'users'

    slack_user_id = models.CharField(max_length=120, unique=True)
    slack_team = models.ForeignKey(Team, on_delete=models.CASCADE)
    slack_dm_channel_id = models.CharField(max_length=120, unique=True)
    email = models.EmailField()
    fyle_refresh_token = models.TextField()
    fyle_user_id = models.CharField(max_length=120, unique=True)
    fyle_org_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return "{} - {}".format(self.slack_user_id, self.email)
