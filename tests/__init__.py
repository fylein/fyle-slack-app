import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'fyle_slack_service.settings'
django.setup()
