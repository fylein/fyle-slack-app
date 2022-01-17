import os
import psycopg2
import csv
import requests
import time

from fyle.platform import Platform
from fyle_slack_app.libs import http, assertions, utils


def get_fyle_access_token(fyle_refresh_token: str) -> str:
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': fyle_refresh_token,
        'client_id': os.environ['FYLE_CLIENT_ID'],
        'client_secret': os.environ['FYLE_CLIENT_SECRET']
    }

    headers = {
        'Content-Type': 'application/json'
    }

    oauth_response = requests.post('{}/oauth/token'.format(os.environ['FYLE_ACCOUNTS_URL']), json=payload, headers=headers)
    assertions.assert_good(oauth_response.status_code == 200, 'Error fetching fyle token details')

    return oauth_response.json()['access_token']


def get_cluster_domain(fyle_refresh_token: str) -> str:
    access_token = get_fyle_access_token(fyle_refresh_token)
    cluster_domain_url = '{}/oauth/cluster'.format(os.environ['FYLE_ACCOUNTS_URL'])
    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer {}'.format(access_token)
    }

    response = http.post(url=cluster_domain_url, headers=headers)
    assertions.assert_valid(response.status_code == 200, 'Error fetching cluster domain')

    return response.json()['cluster_domain']


def get_fyle_sdk_connection(refresh_token):
    cluster_domain = get_cluster_domain(refresh_token)
    FYLE_ACCOUNTS_URL = os.environ['FYLE_ACCOUNTS_URL']

    FYLE_PLATFORM_URL = '{}/platform/v1'.format(cluster_domain)
    FYLE_TOKEN_URL = '{}/oauth/token'.format(FYLE_ACCOUNTS_URL)
    FYLE_CLIENT_ID = os.environ['FYLE_CLIENT_ID']
    FYLE_CLIENT_SECRET = os.environ['FYLE_CLIENT_SECRET']

    return Platform(
        server_url=FYLE_PLATFORM_URL,
        token_url=FYLE_TOKEN_URL,
        client_id=FYLE_CLIENT_ID,
        client_secret=FYLE_CLIENT_SECRET,
        refresh_token=refresh_token
    )


def get_fyle_profile(refresh_token):
    connection = get_fyle_sdk_connection(refresh_token)
    fyle_profile_response = connection.v1beta.spender.my_profile.get()
    return fyle_profile_response['data']


def generate_list(slack_users):
    org_id_list = [['fyle_user_id', 'fyle_org_id']]
    
    # Fetch org_id for all users and appending it to a list
    for users in slack_users:
        fyle_user_id = users[0]
        refresh_token = users[1]
        fyle_profile = get_fyle_profile(refresh_token)
        fyle_org_id = fyle_profile['org_id']
        org_id_list.append([fyle_user_id, fyle_org_id])
    
    # Write to a file
    with open('slack_users_org_id_list.csv', 'w') as csvfile: 
        # creating a csv writer object 
        csvwriter = csv.writer(csvfile) 
        
        # writing the data rows 
        csvwriter.writerows(org_id_list)


def get_slack_users_data():
    query = 'select fyle_user_id, fyle_refresh_token from users;'

    # connect to prod-US db
    con_prod_us = psycopg2.connect(database=os.environ['DB_NAME'], user=os.environ['PROD_USER'], password=os.environ['PROD_US_PASS'], host=os.environ['PROD_US_HOST'], port="5432")
    cursor_us = con_prod_us.cursor()
    cursor_us.execute(query)
    slack_users = cursor_us.fetchall()

    cursor_us.close()
    con_prod_us.close()

    print('Data successfuly fetched from slack DB')
    return slack_users


def do_magic():
    slack_users = get_slack_users_data()
    generate_list(slack_users)
    print('List Generated Successfully!')


if __name__ == '__main__':
    begin = time.time()
    do_magic()
    end = time.time()
    print('\nTime taken = {}'.format(end-begin))