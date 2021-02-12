from django.db import models

from . import SlackTeam

class SlackUser(models.Model):

    class Meta:
        db_table = 'slack_users'
    
    id = models.CharField(max_length=120, primary_key=True)
    slack_team_id = models.ForeignKey(SlackTeam, on_delete=models.CASCADE)
    dm_channel_id = models.CharField(max_length=120, unique=True)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} - {}".format(self.id, self.email)
