# pylint: skip-file
import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(BASE_DIR)

# Since this file lies outside django project scope
# we need to setup django to import django modules, ex: models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fyle_slack_service.settings')
django.setup()


from fyle_slack_app.fyle.authorization.views import FyleAuthorization
from fyle_slack_app.models import User
from fyle_slack_app.fyle import utils as fyle_utils
from fyle_slack_app.libs import logger


logger = logger.get_logger(__name__)


users = User.objects.all()
users_count = users.count()

logger.info('Starting to create subscription for users: %s', users_count)

failed_users = []

for user in users:
    try:

        fyle_profile = fyle_utils.get_fyle_profile(user.fyle_refresh_token)

        # Creating subscription for user
        FyleAuthorization().create_notification_subscription(user, fyle_profile)

    except Exception as err:

        failed_users.append(user.fyle_user_id)

        logger.info('\nError while creating subscription for user %s - %s', user.slack_user_id, user.fyle_user_id)
        logger.info('\nError -> %s', err)


if len(failed_users) == 0:
    logger.info('Subscriptions created successfully for all users: %s', users_count)
else:
    logger.info('Subscriptions created successfully for users: %s', users_count - len(failed_users))
    logger.info('Subscriptions created successfully for users: %s', failed_users)
