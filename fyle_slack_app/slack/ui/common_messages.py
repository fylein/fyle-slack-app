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
