from typing import Dict

import requests


from fyle.platform import Platform

from django.conf import settings

from fyle_slack_app.libs import http, assertions, utils
from fyle_slack_app.models.user_subscription_details import SubscriptionType


FYLE_TOKEN_URL = '{}/oauth/token'.format(settings.FYLE_ACCOUNTS_URL)


def get_fyle_sdk_connection(refresh_token: str) -> Platform:
    # access_token = get_fyle_access_token(refresh_token)
    cluster_domain = get_cluster_domain(refresh_token)

    FYLE_PLATFORM_URL = '{}/platform/v1'.format(cluster_domain)

    return Platform(
        server_url=FYLE_PLATFORM_URL,
        token_url=FYLE_TOKEN_URL,
        client_id=settings.FYLE_CLIENT_ID,
        client_secret=settings.FYLE_CLIENT_SECRET,
        refresh_token=refresh_token
    )

@utils.cache_this(timeout=60)
def get_cluster_domain(fyle_refresh_token: str) -> str:
    print('INSIDE CLUSTER DOMAIN')
    access_token = get_fyle_access_token(fyle_refresh_token)
    cluster_domain_url = '{}/oauth/cluster'.format(settings.FYLE_ACCOUNTS_URL)
    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer {}'.format(access_token)
    }

    response = http.post(url=cluster_domain_url, headers=headers)
    assertions.assert_valid(response.status_code == 200, 'Error fetching cluster domain')

    return response.json()['cluster_domain']


def get_fyle_access_token(fyle_refresh_token: str) -> str:
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


def get_fyle_refresh_token(code: str) -> str:
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


@utils.cache_this()
def get_fyle_profile(refresh_token: str) -> Dict:
    print('MY PROFILE')
    connection = get_fyle_sdk_connection(refresh_token)
    fyle_profile_response = connection.v1.fyler.my_profile.get()
    return fyle_profile_response['data']


def get_fyle_resource_url(fyle_refresh_token: str, resource: Dict, resource_type: str) -> str:
    # access_token = get_fyle_access_token(fyle_refresh_token)
    cluster_domain = get_cluster_domain(fyle_refresh_token)

    RESOURCE_URL_MAPPING = {
        'REPORT': '{}/app/main/#/enterprise/reports'.format(cluster_domain),
        'EXPENSE': '{}/app/main/#/enterprise/view_expense'.format(cluster_domain)
    }

    resource_base_url = RESOURCE_URL_MAPPING[resource_type]
    resource_base_url = '{}/{}'.format(resource_base_url, resource['id'])

    resource_query_params = {
        'org_id': resource['org_id']
    }

    resource_url = utils.convert_to_branchio_url(resource_base_url, resource_query_params)

    return resource_url


def get_fyle_oauth_url(user_id: str, team_id: str) -> str:
    state_params = {
        'user_id': user_id,
        'team_id': team_id
    }

    base64_encoded_state = utils.encode_state(state_params)

    redirect_uri = '{}/fyle/authorization'.format(settings.SLACK_SERVICE_BASE_URL)

    FYLE_OAUTH_URL = '{}/app/developers/#/oauth/authorize?client_id={}&response_type=code&state={}&redirect_uri={}'.format(
        settings.FYLE_ACCOUNTS_URL,
        settings.FYLE_CLIENT_ID,
        base64_encoded_state,
        redirect_uri
    )

    return FYLE_OAUTH_URL


def upsert_fyle_subscription(cluster_domain: str, access_token: str, subscription_payload: Dict, subscription_type: SubscriptionType) -> requests.Response:
    FYLE_PLATFORM_URL = '{}/platform/v1'.format(cluster_domain)

    SUBSCRIPTION_TYPE_URL_MAPPINGS = {
        SubscriptionType.FYLER_SUBSCRIPTION: '{}/fyler/subscriptions'.format(FYLE_PLATFORM_URL),
        SubscriptionType.APPROVER_SUBSCRIPTION: '{}/approver/subscriptions'.format(FYLE_PLATFORM_URL)
    }

    subscrition_url = SUBSCRIPTION_TYPE_URL_MAPPINGS[subscription_type]

    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer {}'.format(access_token)
    }

    subscription = http.post(
        url=subscrition_url,
        json=subscription_payload,
        headers=headers
    )

    return subscription
