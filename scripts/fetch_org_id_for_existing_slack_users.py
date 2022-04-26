import os
import sys
import csv
import time
import django
from fyle.platform import Platform

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(BASE_DIR)

# Since this file lies outside django project scope
# we need to setup django to import django modules, ex: models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fyle_slack_service.settings')
django.setup()

from fyle_slack_app.models import User
from fyle_slack_app.fyle import utils as fyle_utils


def get_cluster_domain(fyle_user_id):
    # Fetch the list of user_id of all existing slack users separately for both DBs
    us_users = []
    in_users = []
    
    if fyle_user_id in us_users:
        return 'https://us1.fylehq.com'
    elif fyle_user_id in in_users:
        return 'https://in1.fylehq.com'
    else:
        return None


def get_fyle_sdk_connection(refresh_token, fyle_user_id):
    cluster_domain = get_cluster_domain(fyle_user_id)
    if cluster_domain is None:
        return None

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


def get_fyle_profile(refresh_token, fyle_user_id):
    connection = get_fyle_sdk_connection(refresh_token, fyle_user_id)
    if connection is None:
        return None
    fyle_profile_response = connection.v1beta.spender.my_profile.get()
    return fyle_profile_response['data']


def generate_list(slack_users):
    org_id_list = [['fyle_user_id', 'fyle_org_id']]
    
    csvfile = open("slack_users_org_id_list.txt", "w")
    # creating a csv writer object 
    csvwriter = csv.writer(csvfile)

    counter = 1

    # Fetch org_id for all users and appending it to a list
    for users in slack_users:
        fyle_user_id = users[0]
        refresh_token = users[1]
        fyle_profile = get_fyle_profile(refresh_token, fyle_user_id)
        if fyle_profile is None:
            continue
        fyle_org_id = fyle_profile['org_id']
        csvwriter.writerow([fyle_user_id, fyle_org_id])

        print(f'User {counter} completed')
        counter += 1

    csvfile.close()


def get_slack_users_data():
    users = list(User.objects.values_list('fyle_user_id', 'fyle_refresh_token'))
    print('Data successfuly fetched from slack DB')
    return users


def do_magic():
    slack_users = get_slack_users_data()
    generate_list(slack_users)
    print('\nList Generated Successfully!')


if __name__ == '__main__':
    begin = time.time()
    do_magic()
    end = time.time()
    print('\nTime taken = {}'.format(end-begin))
