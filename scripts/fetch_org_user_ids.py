import os
import psycopg2
import csv

# installed pyjwt
import jwt 


def fetch_org_user_id(refresh_token):
    # Decoding only the jwt payload here, instead of using secret key to verify :P
    decoded_data = jwt.decode(refresh_token, algorithms=['HS256'], options={"verify_signature": False})
    org_user_id = decoded_data['org_user_id']
    return org_user_id


def generate_list(slack_users):
    org_user_id_list = [['fyle_user_id', 'org_user_id']]
    
    # Fetch org_user_id for all users and appending it to a list
    for users in slack_users:
        fyle_user_id = users[0]
        refresh_token = users[1]
        org_user_id = fetch_org_user_id(refresh_token).strip('"')
        
        org_user_id_list.append([fyle_user_id, org_user_id])
    
    # Write to a file
    with open('org_user_id_list.csv', 'w') as csvfile: 
        # creating a csv writer object 
        csvwriter = csv.writer(csvfile) 
        
        # writing the data rows 
        csvwriter.writerows(org_user_id_list)


def get_slack_users_data():
    query = 'select fyle_user_id, fyle_refresh_token from users;'

    # connect to prod-US db
    con_prod_us = psycopg2.connect(database=os.environ['DB_NAME'], user=os.environ['PROD_USER'], password=os.environ['PROD_US_PASS'], host=os.environ['PROD_US_HOST'], port="5432")
    cursor_us = con_prod_us.cursor()
    cursor_us.execute(query)
    slack_users = cursor_us.fetchall()

    cursor_us.close()
    con_prod_us.close()

    return slack_users


def do_magic():
    slack_users = get_slack_users_data()
    generate_list(slack_users)
    print('List Generated Successfully!')


if __name__ == '__main__':
    do_magic()