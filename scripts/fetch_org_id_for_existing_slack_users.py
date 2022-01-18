import os
import sys
import csv
import time
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(BASE_DIR)

# Since this file lies outside django project scope
# we need to setup django to import django modules, ex: models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fyle_slack_service.settings')
django.setup()

from fyle_slack_app.models import User
from fyle_slack_app.fyle import utils as fyle_utils


def generate_list(slack_users):
    org_id_list = [['fyle_user_id', 'fyle_org_id']]
    
    counter = 1

    # Fetch org_id for all users and appending it to a list
    for users in slack_users:
        fyle_user_id = users[0]
        refresh_token = users[1]
        fyle_profile = fyle_utils.get_fyle_profile(refresh_token)
        fyle_org_id = fyle_profile['org_id']
        org_id_list.append([fyle_user_id, fyle_org_id])

        print('User no. {} completed'.format(counter))
        counter += 1
    
    # Write to a file
    with open('slack_users_org_id_list.csv', 'w') as csvfile: 
        # creating a csv writer object 
        csvwriter = csv.writer(csvfile) 
        
        # writing the data rows 
        csvwriter.writerows(org_id_list)


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