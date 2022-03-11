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
            'text': 'Approving :hourglass_flowing_sand:',
            'emoji': True
        },
        'action_id': 'pre_auth_message_approve',
        'value': 'pre_auth_message_approve',
    }
}


def get_no_report_access_message(notification_message: List[Dict]) -> List[Dict]:
    # Removing CTAs from notification message for deleted report
    
    report_notification_message = []
    for message_block in notification_message:
        if message_block['type'] != 'actions':
            report_notification_message.append(message_block)

    report_message = 'Looks like you no longer have access to this expense report :face_with_head_bandage:'
    report_deleted_section = {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': report_message
        }
    }
    report_notification_message.insert(3, report_deleted_section)

    return report_notification_message