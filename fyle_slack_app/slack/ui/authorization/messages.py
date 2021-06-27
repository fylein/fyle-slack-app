from typing import Dict, List


def get_pre_authorization_message(user_name: str, FYLE_OAUTH_URL: str) -> List[Dict]:
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
                'text': 'The Fyle app for Slack brings all the important expense reporting action to right where work happens. No more switching between multiple tabs! '
            }
        },
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': 'Once you link your Fyle account, you can use this app to receive real-time notifications on the status of your expense reports after you\'ve submitted them.'
            }
        },
		{
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': 'And if you\'re an approver, you\'ll be notified on Slack whenever a teammate submits an expense report to you. Not just that, you can even approve it right from this app. Your teammates are going to love you for your speed! :zap:'
            }
        },
		{
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': 'What are you waiting for? \n Link your Fyle account now'
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
				'text': 'Yaay :tada: you\'ve successfully linked *Fyle* to Slack :confetti_ball:  \n\n'
			}
		},
		{
			'type': 'section',
			'text': {
				'type': 'mrkdwn',
				'text': '*What\'s next?*'
			}
		},
		{
			'type': 'section',
			'text': {
				'type': 'mrkdwn',
				'text': 'If you\'ve submitted an expense report for approval, you\'ll receive real-time notifications on the Fyle Slack app whenever:'
			}
		},
		{
			'type': 'section',
			'text': {
				'type': 'mrkdwn',
				'text': '• Your report gets approved :white_check_mark: \n • You receive your reimbursement :moneybag: \n • A comment is made on the report :speech_balloon: \n • The report is sent back to you for further inquiry :bangbang: '
			}
		},
		{
			'type': 'section',
			'text': {
				'type': 'mrkdwn',
				'text': 'If you\'re an approver, you\'ll see a direct message like below whenever your teammate submits a report to you for approval.'
			}
		},
		{
			'type': 'image',
			'image_url': 'https://i.ibb.co/1zY81f7/Screenshot-2021-03-01-at-12-00-25-PM.png',
			'alt_text': 'inspiration'
		},
		{
			'type': 'section',
			'text': {
				'type': 'mrkdwn',
				'text': 'You can even approve the report from within the Slack app as soon as you\'re notified. Your teammates are going to love you for your speed! :zap:'
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
