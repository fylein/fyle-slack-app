from fyle_slack_app.slack.ui import feedbacks

class TestFeedbackMessages:

    def test_get_user_feedback_message(self):
        feedback_trigger = 'fake_feedback_trigger'
        feedback_message_blocks = feedbacks.messages.get_user_feedback_message(feedback_trigger)
        assert feedback_message_blocks[1]['elements'][0]['value'] == feedback_trigger

    def test_get_post_feedback_submission_message(self):
        feedback_message_blocks = feedbacks.messages.get_post_feedback_submission_message()
        assert feedback_message_blocks[0]['text']['text'] == 'Thanks for submitting the feedback :rainbow:'

    def test_get_feedback_dialog(self):
        private_metadata = 'fake_private_metadata'
        feedback_dialog = feedbacks.messages.get_feedback_dialog(private_metadata)
        feedback_rating_options = feedback_dialog['blocks'][2]['element']['options']
        for rating in range(10):
            assert feedback_rating_options[rating]['text']['text'] == '{} :star:'.format(rating+1)
            assert feedback_rating_options[rating]['value'] == str(rating+1)