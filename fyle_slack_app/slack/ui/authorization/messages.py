
from typing import Dict, List


def get_pre_authorization_message(user_name, FYLE_OAUTH_URL) -> List[Dict]:
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
                    'url': FYLE_OAUTH_URL,
                    'style': 'primary',
                    'value': 'link_fyle_account',
                    'action_id': 'link_fyle_account'
                }
            ]
        }
    ]


def get_post_authorization_message() -> List[Dict]:
    return [
		{
			'type': 'section',
			'text': {
				'type': 'mrkdwn',
				'text': 'Yaay :tada: you\'ve linked *Fyle* to Slack :confetti_ball:  \n\n'
			}
		},
		{
			'type': 'section',
			'text': {
				'type': 'mrkdwn',
				'text': '*What to do next?*'
			}
		},
		{
			'type': 'section',
			'text': {
				'type': 'mrkdwn',
				'text': 'When one of your teammates submits an expense report for your approval, you\'ll receive a direct message like this:'
			}
		},
		{
			'type': 'image',
			'image_url': 'https://i.ibb.co/p4q5XSC/Screen-Shot-2021-01-20-at-4-46-34-PM.png',
			'alt_text': 'inspiration'
		},
		{
			'type': 'section',
			'text': {
				'type': 'mrkdwn',
				'text': 'You can approve reports within Slack or view details in Fyle within 2 seconds. Your teammates are going to love you a little bit more!'
			}
		},
		{
			'type': 'section',
			'text': {
				'type': 'mrkdwn',
				'text': '*Coming soon* \n •  Submit your expenses from Slack'
			}
		},
		{
			'type': 'divider'
		},
		{
			'type': 'section',
			'text': {
				'type': 'mrkdwn',
				'text': 'To see the official documentation, visit https://www.fylehq.com/help/en/?q=slack \nIf you\'re running into any trouble, please send us a note at support@fylehq.com'
			}
		}
	]
