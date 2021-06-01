from django.conf import settings

from fyle_slack_app.libs import utils, assertions, logger
from fyle_slack_app.slack import utils as slack_utils
from fyle_slack_app.fyle import utils as fyle_utils
from fyle_slack_app.models import User
from fyle_slack_app.slack.commands.handlers import SlackCommandHandler


logger = logger.get_logger(__name__)


def fyle_unlink_account(user_id: str, team_id: str, user_dm_channel_id: str) -> None:
    user = utils.get_or_none(User, slack_user_id=user_id)

    slack_client = slack_utils.get_slack_client(team_id)

    # Text message if user hasn't linked Fyle account
    text = 'Hey buddy, you haven\'t linked your Fyle account yet :face_with_head_bandage: \n' \
        'Checkout home tab for `Link Your Fyle Account` to link your Slack with Fyle :zap:'

    if user is not None:
        is_error_occured = False

        # Disabling user subscription
        access_token = fyle_utils.get_fyle_access_token(user.fyle_refresh_token)
        cluster_domain = fyle_utils.get_cluster_domain(access_token)

        fyle_profile = fyle_utils.get_fyle_profile(user.fyle_refresh_token)

        if 'FYLER' in fyle_profile['roles']:
            webhook_url = '{}/fyle/fyler/notifications/{}'.format(settings.SLACK_SERVICE_BASE_URL, fyle_profile['user_id'])
            query_params = {
                'user_id': 'eq.{}'.format(fyle_profile['user_id']),
                'is_enabled': 'eq.true',
                'webhook_url': 'eq.{}'.format(webhook_url)
            }
            fyler_subscription = fyle_utils.get_fyle_subscription(cluster_domain, access_token, query_params, 'FYLER')

            fyler_subscription_id = fyler_subscription.json()['data'][0]['id']

            fyler_subscription_payload = {}
            fyler_subscription_payload['data'] = {
                'id': fyler_subscription_id,
                'webhook_url': webhook_url,
                'is_enabled': False
            }

            fyler_subscription = fyle_utils.upsert_fyle_subscription(cluster_domain, access_token, fyler_subscription_payload, 'FYLER')

            if fyler_subscription.status_code != 200:
                text = 'Looks like something went wrong :zipper_mouth_face: \n Please try again'
                is_error_occured = True

                logger.error('Error while disabling fyler subscription for user: %s ', fyle_profile['user_id'])
                assertions.assert_good(False)


        if 'APPROVER' in fyle_profile['roles']:
            webhook_url = '{}/fyle/approver/notifications/{}'.format(settings.SLACK_SERVICE_BASE_URL, fyle_profile['user_id'])
            query_params = {
                'approver_user_id': 'eq.{}'.format(fyle_profile['user_id']),
                'is_enabled': 'eq.true',
                'webhook_url': 'eq.{}'.format(webhook_url)
            }
            approver_subscription = fyle_utils.get_fyle_subscription(cluster_domain, access_token, query_params, 'APPROVER')

            approver_subscription_id = approver_subscription.json()['data'][0]['id']

            approver_subscription_payload = {}
            approver_subscription_payload['data'] = {
                'id': approver_subscription_id,
                'webhook_url': webhook_url,
                'is_enabled': False
            }

            approver_subscription = fyle_utils.upsert_fyle_subscription(cluster_domain, access_token, approver_subscription_payload, 'APPROVER')

            if approver_subscription.status_code != 200:
                text = 'Looks like something went wrong :zipper_mouth_face: \n Please try again'
                is_error_occured = True

                logger.error('Error while disabling approver subscription for user: %s ', fyle_profile['user_id'])
                assertions.assert_good(False)

        # Deleting user entry to unlink fyle account
        if is_error_occured is False:
            user.delete()
            text = 'Hey, you\'ve successfully unlinked your Fyle account with slack :white_check_mark:\n ' \
            'If you change your mind about us checkout home tab for `Link Your Fyle Account` to link your Slack with Fyle :zap:'

        # Update home tab with pre auth message
        SlackCommandHandler().update_home_tab_with_pre_auth_message(user_id, team_id)

        # Track Fyle account unlinked
        SlackCommandHandler().track_fyle_account_unlinked(user)

    slack_client.chat_postMessage(
        channel=user_dm_channel_id,
        text=text
    )
