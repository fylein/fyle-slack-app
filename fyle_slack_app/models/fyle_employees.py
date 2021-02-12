from django.db import models


class FyleEmployee(models.Model):
    
    class Meta:
        db_table = 'fyle_employees'

    id = models.CharField(max_length=12, primary_key=True)
    refresh_token = models.TextField()
    email = models.EmailField()
    org_id = models.CharField(max_length=12)
    org_name = models.CharField(max_length=12)
    org_currency = models.CharField(max_length=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} - {}".format(self.id, self.email)