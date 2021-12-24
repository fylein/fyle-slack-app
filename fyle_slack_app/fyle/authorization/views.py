from typing import Dict

import uuid

from django.http import HttpResponseRedirect, HttpRequest
from django.views import View
from django.conf import settings
from django.db import transaction

from slack_sdk.web.client import WebClient

from fyle_slack_app import tracking
from fyle_slack_app.fyle import utils as fyle_utils
from fyle_slack_app.libs import utils, assertions, logger
from fyle_slack_app.models import Team, User, UserSubscriptionDetail
from fyle_slack_app.models.user_subscription_details import SubscriptionType
from fyle_slack_app.slack.utils import get_slack_user_dm_channel_id
from fyle_slack_app.slack.ui.authorization.messages import get_post_authorization_message
from fyle_slack_app.slack.ui.dashboard import messages as dashboard_messages


logger = logger.get_logger(__name__)


class FyleAuthorization(View):

    def get(self, request: HttpRequest) -> HttpResponseRedirect:

        error = request.GET.get('error')
        state = request.GET.get('state')

        state_params = utils.decode_state(state)

        # Fetch the slack team
        slack_team = utils.get_or_none(Team, id=state_params['team_id'])
        assertions.assert_found(slack_team, 'slack team not found')

        # Get slack client
        slack_client = WebClient(token=slack_team.bot_access_token)

        # Fetch slack dm channel
        slack_user_dm_channel_id = get_slack_user_dm_channel_id(slack_client, state_params['user_id'])

        if error:

            logger.error('Fyle authorization error: %s', error)

            error_message = 'Seems like something went wrong :face_with_head_bandage: \n' \
                        'If the issues still persists, please contact support@fylehq.com'

            # Error when user declines Fyle authorization
            if error == 'access_denied':
                error_message = 'Well.. if you do change your mind, visit the home tab and link your Fyle account to Slack to stay up to date on all your expense reports.'

            slack_client.chat_postMessage(
                    channel=slack_user_dm_channel_id,
                    text=error_message
                )
        else:
            code = request.GET.get('code')

            user = utils.get_or_none(User, slack_user_id=state_params['user_id'])

            if user is not None:
                # If the user already exists, send a message to user indicating they've already linked Fyle account
                self.send_linked_account_message(slack_client, slack_user_dm_channel_id)

            else:
                fyle_refresh_token = fyle_utils.get_fyle_refresh_token(code)

                fyle_profile = fyle_utils.get_fyle_profile(fyle_refresh_token)

                fyle_user = utils.get_or_none(User, fyle_user_id=fyle_profile['user_id'])

                if fyle_user is not None:
                    # If the fyle user already exists, send a message to user indicating they've already 
                    # linked their Fyle account in one of their slack workspace
                    team_name = fyle_user.slack_team.name
                    self.send_linked_account_message(slack_client, slack_user_dm_channel_id, team_name)
                
                else:
                    # Putting below logic inside a transaction block to prevent bad data
                    # If any error occurs in any of the below step, Fyle account link to Slack should not happen
                    with transaction.atomic():
                        # Create user
                        user = self.create_user(slack_client, slack_team, state_params['user_id'], slack_user_dm_channel_id, fyle_refresh_token, fyle_profile['user_id'])

                        # Creating subscriptions for user
                        self.create_notification_subscription(user, fyle_profile)

                    # Send post authorization message to user
                    self.send_post_authorization_message(slack_client, slack_user_dm_channel_id)

                    # Update user home tab with post auth message
                    self.update_user_home_tab_with_post_auth_message(slack_client, state_params['user_id'])

                    # Track fyle account link to slack
                    self.track_fyle_authorization(user, fyle_profile)

        # Redirecting the user to slack bot when auth is complete
        return HttpResponseRedirect('https://slack.com/app_redirect?app={}'.format(settings.SLACK_APP_ID))


    # pylint: disable=fixme
    # TODO: Refactor `create_user` this takes in `slack_client` which doesn't define the purpose of this function
    def create_user(self, slack_client: WebClient, slack_team: Team, user_id: str, slack_user_dm_channel_id: str, fyle_refresh_token: str, fyle_user_id: str) -> User:

        # Fetch slack user details
        slack_user_info = slack_client.users_info(user=user_id)
        assertions.assert_good(slack_user_info['ok'] is True)

        # Store slack user in DB
        user = User.objects.create(
            slack_user_id=slack_user_info['user']['id'],
            slack_team=slack_team,
            email=slack_user_info['user']['profile']['email'],
            slack_dm_channel_id=slack_user_dm_channel_id,
            fyle_refresh_token=fyle_refresh_token,
            fyle_user_id=fyle_user_id
        )

        return user


    def send_post_authorization_message(self, slack_client: WebClient, slack_user_dm_channel_id: str) -> None:
        post_authorization_message = get_post_authorization_message()
        slack_client.chat_postMessage(
            channel=slack_user_dm_channel_id,
            blocks=post_authorization_message
        )


    def send_linked_account_message(self, slack_client: WebClient, slack_user_dm_channel_id: str, workspace_name: str = None) -> None:
        if workspace_name is not None:
            message = f'Hey buddy you\'ve already linked your *Fyle* account in this workspace `{workspace_name}` :rainbow:'
        else:
            message = 'Hey buddy you\'ve already linked your *Fyle* account :rainbow:'
        
        slack_client.chat_postMessage(
            channel=slack_user_dm_channel_id,
            text=message
        )


    def update_user_home_tab_with_post_auth_message(self, slack_client: WebClient, user_id: str) -> None:
        post_authorization_message_view = dashboard_messages.get_post_authorization_message()
        slack_client.views_publish(user_id=user_id, view=post_authorization_message_view)


    def create_notification_subscription(self, user: User, fyle_profile: Dict) -> None:
        access_token = fyle_utils.get_fyle_access_token(user.fyle_refresh_token)
        cluster_domain = fyle_utils.get_cluster_domain(user.fyle_refresh_token)

        SUBSCRIPTON_WEBHOOK_DETAILS_MAPPING = {
            SubscriptionType.FYLER_SUBSCRIPTION: {
                'role_required': 'FYLER',
                'webhook_url': '{}/fyle/fyler/notifications'.format(settings.SLACK_SERVICE_BASE_URL)
            },
            SubscriptionType.APPROVER_SUBSCRIPTION: {
                'role_required': 'APPROVER',
                'webhook_url': '{}/fyle/approver/notifications'.format(settings.SLACK_SERVICE_BASE_URL)
            }
        }

        user_subscription_details = []

        for subscription_type in SubscriptionType:
            subscription_webhook_details = SUBSCRIPTON_WEBHOOK_DETAILS_MAPPING[subscription_type]

            subscription_role_required = subscription_webhook_details['role_required']

            if subscription_role_required in fyle_profile['roles']:
                fyle_user_id = user.fyle_user_id

                subscription_webhook_id = str(uuid.uuid4())

                webhook_url = subscription_webhook_details['webhook_url']
                webhook_url = '{}/{}'.format(webhook_url, subscription_webhook_id)

                subscription_payload = {}
                subscription_payload['data'] = {
                    'webhook_url': webhook_url,
                    'is_enabled': True
                }

                subscription = fyle_utils.upsert_fyle_subscription(cluster_domain, access_token, subscription_payload, subscription_type)

                if subscription.status_code != 200:
                    logger.error('Error while creating %s subscription for user: %s ', subscription_role_required, fyle_user_id)
                    logger.error('%s Subscription error %s', subscription_role_required, subscription.content)
                    assertions.assert_good(False)

                subscription_id = subscription.json()['data']['id']

                subscription_detail = UserSubscriptionDetail(
                    slack_user=user,
                    subscription_type=subscription_type.value,
                    subscription_id=subscription_id,
                    webhook_id=subscription_webhook_id
                )

                user_subscription_details.append(subscription_detail)

        # Creating/Inserting subsctiptions in bulk
        UserSubscriptionDetail.objects.bulk_create(user_subscription_details)


    def track_fyle_authorization(self, user: User, fyle_profile: Dict) -> None:
        event_data = {
            'asset': 'SLACK_APP',
            'slack_user_id': user.slack_user_id,
            'fyle_user_id': user.fyle_user_id,
            'email': user.email,
            'slack_team_id': user.slack_team.id,
            'slack_team_name': user.slack_team.name,
            'fyle_roles': fyle_profile['roles']
        }

        tracking.identify_user(user.email)

        tracking.track_event(user.email, 'Fyle Account Linked To Slack', event_data)
