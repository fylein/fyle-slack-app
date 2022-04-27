from typing import Dict, List
from fyle_slack_app.slack import utils as slack_utils

IN_PROGRESS_MESSAGE = {
    slack_utils.AsyncOperation.UNLINKING_ACCOUNT.value: {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': 'Your request of `Unlink Fyle Account` is being processed :hourglass_flowing_sand:'
        }
    },
    slack_utils.AsyncOperation.APPROVING_REPORT.value: {
        'type': 'button',
        'style': 'primary',
        'text': {
            'type': 'plain_text',
            'text': ':hourglass_flowing_sand: Approving',
            'emoji': True
        },
        'action_id': 'pre_auth_message_approve',
        'value': 'pre_auth_message_approve',
    }
}


def get_custom_text_section_block(message: str) -> List[Dict]:
    section_block = [{
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': message
        }
    }]
    return section_block


def get_updated_approval_notification_message(notification_message: List[Dict], custom_message: str, cta: bool) -> List[Dict]:
    report_notification_message = []
    for message_block in notification_message:
        if cta is False and message_block['type'] == 'actions':
            continue
        report_notification_message.append(message_block)

    report_section = {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': custom_message
        }
    }
    report_notification_message.insert(3, report_section)

    return report_notification_message
