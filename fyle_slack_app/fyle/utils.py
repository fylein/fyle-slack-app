import requests

from fyle.platform import Platform
from fyle.platform import exceptions

from slack_sdk.web import WebClient

from django.conf import settings

from fyle_slack_app.libs import http, assertions, utils, logger
from fyle_slack_app.models import User


logger = logger.get_logger(__name__)


FYLE_TOKEN_URL = '{}/oauth/token'.format(settings.FYLE_ACCOUNTS_URL)


def get_fyle_sdk_connection(refresh_token):
    try:
        connection = Platform(
            server_url=settings.FYLE_PLATFORM_URL,
            token_url=FYLE_TOKEN_URL,
            client_id=settings.FYLE_CLIENT_ID,
            client_secret=settings.FYLE_CLIENT_SECRET,
            refresh_token=refresh_token
        )
    except exceptions.ExpiredTokenError as error:
        user = utils.get_or_none(User, fyle_refresh_token=refresh_token)
        assertions.assert_found(user, 'User not found')

        logger.error('Error : %s', error)
        logger.error('Token expired for user %s - %s', user.slack_user_id, user.fyle_employee_id)

        # Sending a message to user to start fyle auth process again
        slack_client = WebClient(token=user.slack_team.bot_access_token)

        slack_client.chat_postMessage(
            channel=user.slack_dm_channel_id,
            text='Hey buddy, you\'ll need to link your Fyle account again'
        )

        # Deleting user
        # To fetch new token user will start fyle auth process again
        user.delete()

        # Raising assertion error to stop the request here
        assertions.assert_true(False, 'Fyle token expired', status_code=498)

    return connection


def get_cluster_domain(access_token):
    cluster_domain_url = '{}/oauth/cluster'.format(settings.FYLE_ACCOUNTS_URL)
    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer {}'.format(access_token)
    }

    response = http.post(url=cluster_domain_url, headers=headers)
    assertions.assert_valid(response.status_code == 200, 'Error fetching cluster domain')

    return response.json()['cluster_domain']


def get_fyle_access_token(fyle_refresh_token):
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': fyle_refresh_token,
        'client_id': settings.FYLE_CLIENT_ID,
        'client_secret': settings.FYLE_CLIENT_SECRET
    }

    headers = {
        'Content-Type': 'application/json'
    }

    oauth_response = requests.post('{}/oauth/token'.format(settings.FYLE_ACCOUNTS_URL), json=payload, headers=headers)
    assertions.assert_good(oauth_response.status_code == 200, 'Error fetching fyle token details')

    return oauth_response.json()['access_token']


def get_fyle_refresh_token(code):
    FYLE_OAUTH_TOKEN_URL = '{}/oauth/token'.format(settings.FYLE_ACCOUNTS_URL)

    oauth_payload = {
        'grant_type': 'authorization_code',
        'client_id': settings.FYLE_CLIENT_ID,
        'client_secret': settings.FYLE_CLIENT_SECRET,
        'code': code
    }

    oauth_response = http.post(FYLE_OAUTH_TOKEN_URL, oauth_payload)
    assertions.assert_good(oauth_response.status_code == 200, 'Error fetching fyle token details')

    return oauth_response.json()['refresh_token']


def get_fyle_profile(refresh_token):
    connection = get_fyle_sdk_connection(refresh_token)
    fyle_profile_response = connection.v1.fyler.my_profile.get()
    return fyle_profile_response['data']


def get_fyle_report_url(fyle_refresh_token):
    access_token = get_fyle_access_token(fyle_refresh_token)
    cluster_domain = get_cluster_domain(access_token)
    return '{}/app/main/#/enterprise/reports'.format(cluster_domain)
