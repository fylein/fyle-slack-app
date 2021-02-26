# This is needed because we're doing test outside django's scope i.e. in a separate tests folder in root directory.
# And we're importing few django settings in testcase file.
# So in order to import django setting we need to initialize test directory with django settings module.

import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'fyle_slack_service.settings'
django.setup()
