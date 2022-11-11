from fyle_slack_app.slack.ui import common_messages

class TestCommonMessages:

    def test_get_custom_text_section_block(self):
        MESSAGE = "Hi there, I am using fyle"
        section_block = common_messages.get_custom_text_section_block(message=MESSAGE)
        assert section_block[0]['text']['text'] == MESSAGE
    
    def test_get_updated_approval_notification_message(self):
        FAKE_NOTIFICATION_MESSAGES = [{
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': 'Hey there'
                }
            },
            {
            'type': 'actions',
            'text': {
                'type': 'mrkdwn',
                'text': 'Hey    there'
                }
            }
        ]
        FAKE_CUSTOM_MESSAGE = 'Hello World'
        report_notification_message1 = common_messages.get_updated_approval_notification_message(FAKE_NOTIFICATION_MESSAGES, FAKE_CUSTOM_MESSAGE, True)
        report_notification_message2 = common_messages.get_updated_approval_notification_message(FAKE_NOTIFICATION_MESSAGES, FAKE_CUSTOM_MESSAGE, False)
        assert report_notification_message1[-1]['text']['text'] == FAKE_CUSTOM_MESSAGE
        assert report_notification_message2[-1]['text']['text'] == FAKE_CUSTOM_MESSAGE

        for notification_message in report_notification_message2:
            if 'type' in notification_message:
                assert notification_message['type'] != 'actions'
