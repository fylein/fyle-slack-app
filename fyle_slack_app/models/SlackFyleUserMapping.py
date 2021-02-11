from django.db import models

from . import SlackUser, FyleEmployee

class SlackFyleUserMapping(models.Model):
    
    class Meta:
        db_table = 'slack_fyle_user_mappings'
    
    slack_user_id = models.ForeignKey(SlackUser, on_delete=models.CASCADE)
    fyle_employee_id = models.ForeignKey(FyleEmployee, on_delete=models.CASCADE)

    def __str__(self):
        return "{} - {}".format(self.slack_user_id, self.fyle_employee_id)