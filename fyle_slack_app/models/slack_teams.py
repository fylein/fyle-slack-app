from django.db import models

class SlackTeam(models.Model):
    
    class Meta:
        db_table = 'slack_teams'

    id = models.CharField(max_length=120, primary_key=True)
    name = models.CharField(max_length=120)
    bot_user_id = models.CharField(max_length=120)
    bot_access_token = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} - {}".format(self.id, self.name)