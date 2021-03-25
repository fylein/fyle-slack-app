from fyle_slack_app.slack.ui.authorization import messages


def get_pre_authorization_message(user_name, fyle_oauth_url):
    pre_authorization_message_blocks = messages.get_pre_authorization_message(user_name, fyle_oauth_url)
    return {
        'type': 'home',
        'blocks': pre_authorization_message_blocks
    }


def get_post_authorization_message():
    post_authorization_message_blocks = messages.get_post_authorization_message()
    return {
        'type': 'home',
        'blocks': post_authorization_message_blocks
    }
