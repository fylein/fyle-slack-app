import datetime

from django.conf import settings

def get_report_approval_notification_message(report):
    # BASE_URL needs to be cluster domain
    REPORT_WEBAPP_URL = '{}/app/main/#/enterprise/reports/{}?org_id={}'.format(settings.FYLE_ACCOUNTS_URL, report['id'], report['org_id'])

    submitted_at = datetime.datetime.fromisoformat(report['submitted_at'])
    readable_submitted_at = submitted_at.strftime('%B %d, %Y')

    return [
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': '*{}* submitted an expense report [{}] for your approval'.format(report['employee']['user']['full_name'], report['claim_number'])
            }
        },
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': '*{}*'.format(report['purpose'])
            }
        },
        {
            'type': 'section',
            'fields': [
                {
                    'type': 'mrkdwn',
                    'text': '*Amount:* {} {} \n *No. of expenses:* {}'.format(report['currency'], report['amount'], report['num_expenses'])
                },
                {
                    'type': 'mrkdwn',
                    'text': '*Submitted On:* {}'.format(readable_submitted_at)
                }
            ]
        },
        {
            'type': 'actions',
            'elements': [
                {
                    'type': 'button',
                    'style': 'primary',
                    'text': {
                        'type': 'plain_text',
                        'text': 'Approve',
                        'emoji': True
                    },
                    'action_id': 'report_approve',
                    'value': report['id'],
                },
                {
                    'type': 'button',
                    'text': {
                        'type': 'plain_text',
                        'text': 'Review in Fyle',
                        'emoji': True
                    },
                    'action_id': 'report_review_in_fyle',
                    'url': REPORT_WEBAPP_URL
                }
            ]
        }
    ]