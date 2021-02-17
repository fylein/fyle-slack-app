from django.db import models

from . import Team

class User(models.Model):

    class Meta:
        db_table = 'users'
    
    slack_user_id = models.CharField(max_length=120, primary_key=True)
    slack_team = models.ForeignKey(Team, on_delete=models.CASCADE)
    slack_dm_channel_id = models.CharField(max_length=120, unique=True)
    email = models.EmailField()
    fyle_refresh_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} - {}".format(self.slack_user_id, self.email)