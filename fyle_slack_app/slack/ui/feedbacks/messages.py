from typing import Dict, List


def get_user_feedback_message(feedback_trigger: str) -> List[Dict]:
    feedback_message_blocks = [
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': 'Hey there :wave: please give us some thoughts on how do you feel about this slack app'
            }
        },
        {
            'type': 'actions',
            'elements': [
                {
                    'type': 'button',
                    'style': 'primary',
                    'text': {
                        'type': 'plain_text',
                        'text': 'Give Feedback',
                    },
                    'value': feedback_trigger,
                    'action_id': 'open_feedback_dialog'
                }
            ]
        }
    ]
    return feedback_message_blocks


def get_feedback_dialog(private_metadata: str) -> Dict:
    feedback_dialog = {
        'type': 'modal',
        'callback_id': 'feedback_submission',
        'private_metadata': private_metadata,
        'title': {
            'type': 'plain_text',
            'text': 'Feedback',

        },
        'submit': {
            'type': 'plain_text',
            'text': 'Submit',

        },
        'close': {
            'type': 'plain_text',
            'text': 'Cancel',

        },
        'blocks': [
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': 'Please provide your valueable feedback and help us improve :rocket: '
                }
            },
            {
                'type': 'divider'
            },
            {
                'type': 'section',
                'block_id': 'rating_block',
                'text': {
                    'type': 'mrkdwn',
                    'text': 'How likely are you to recommend Fyle slack app to a friend or colleague?'
                },
                'accessory': {
                    'type': 'static_select',
                    'placeholder': {
                        'type': 'plain_text',
                        'text': 'Rating',
                    },
                    'initial_option': {
                        'text': {
                            'type': 'plain_text',
                            'text': '1 :star: ',

                        },
                        'value': 'value-0'
                    },
                    'options': [
                        {
                            'text': {
                                'type': 'plain_text',
                                'text': '1 :star: ',
                            },
                            'value': 'value-0'
                        },
                    ],
                    'action_id': 'rating'
                }
            },
            {
                'type': 'divider'
            },
            {
                'type': 'input',
                'block_id': 'comment_block',
                'optional': True,
                'element': {
                    'type': 'plain_text_input',
                    'multiline': True,
                    'action_id': 'comment'
                },
                'label': {
                    'type': 'plain_text',
                    'text': 'Please tell us why you gave this score',
                }
            }
        ]
    }
    return feedback_dialog
