
from typing import Dict, List


def get_pre_authorization_message(user_name) -> List[Dict]:
    return [
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': 'Hey there *{}* :wave:'.format(user_name)
            }
        },
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': 'Your organisation uses *Fyle* so you spend virtually no time on expense reports. That\'s some boring work.'
            }
        },
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': 'Once you link your Fyle account, you\'ll see alerts for reports that need your approval and you\'ll able to check and approve them from within Slack. Your teammates will love you for approving their reports in a jiffy!'
            }
        },
        {
            'type': 'actions',
            'elements': [
                {
                    'type': 'button',
                    'text': {
                        'type': 'plain_text',
                        'text': 'Link Your Fyle Account',
                        'emoji': True
                    },
                    'style': 'primary',
                    'value': 'link_fyle_account',
                    'action_id': 'link_fyle_account'
                }
            ]
        }
    ]