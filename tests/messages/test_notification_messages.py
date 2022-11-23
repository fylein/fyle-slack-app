from fyle_slack_app.slack.ui.notifications import messages
from .fixtures import data as expense_data
from fyle_slack_app.slack import utils as slack_utils

class TestNotifications:
    def test_get_expense_view_in_fyle_action(self):
        FAKE_EXPENSE_URL, FAKE_BUTTON_TEXT, FAKE_EXPENSE_ID = ('https://expense-url.com', 'FAKE_BUTTON_TEXT', 1)
        expense_view = messages.get_expense_view_in_fyle_action(FAKE_EXPENSE_URL, FAKE_BUTTON_TEXT, FAKE_EXPENSE_ID)
        assert expense_view['url'] == FAKE_EXPENSE_URL and expense_view['value'] == FAKE_EXPENSE_ID

    def test_get_expense_section_blocks(self):
        FAKE_EXPENSE, FAKE_TITLE_TEXT = expense_data['FAKE_EXPENSE'], 'fake title text'
        expense_section_block = messages.get_expense_section_blocks(FAKE_TITLE_TEXT, FAKE_EXPENSE)
        assert expense_section_block[0]['text']['text'] == 'fake title text'
        assert expense_section_block[1]['fields'][0]['text'] == '*Amount:*\n $100.00 \n ($100.00)'
        assert expense_section_block[1]['fields'][1]['text'] == '*Category:*\n food / Chinese'
        assert expense_section_block[2]['fields'][0]['text'] == '*Merchant:*\n Uber'
        assert expense_section_block[2]['fields'][1]['text'] == '*Purpose:*\n Client Meeting'
        assert expense_section_block[3]['fields'][0]['text'] == '*Project:*\n Backend Development / Fyle Slack App'

    def test_get_expense_commented_notification(self):
        FAKE_EXPENSE, FAKE_USER_DISPLAY_NAME = expense_data['FAKE_EXPENSE'], 'fake-name'
        FAKE_EXPENSE_URL, FAKE_EXPENSE_COMMENT = 'https://fakeurl.com', 'fake-expense-comment'
        expense_section_block, title_text = messages.get_expense_commented_notification(
                FAKE_EXPENSE, FAKE_USER_DISPLAY_NAME, FAKE_EXPENSE_URL, FAKE_EXPENSE_COMMENT
            )
        assert title_text == f':speech_balloon:  *{FAKE_USER_DISPLAY_NAME}* (fake@gmail.com) commented on your expense <{FAKE_EXPENSE_URL}|[1]> '
        assert expense_section_block[2]['fields'][0]['text'] == '*Amount:*\n $100.00 \n ($100.00)'
        assert expense_section_block[2]['fields'][1]['text'] == '*Category:*\n food / Chinese'
        assert expense_section_block[3]['fields'][0]['text'] == '*Merchant:*\n Uber'
        assert expense_section_block[3]['fields'][1]['text'] == '*Purpose:*\n Client Meeting'
        assert expense_section_block[4]['fields'][0]['text'] == '*Project:*\n Backend Development / Fyle Slack App'
        assert expense_section_block[5]['elements'][0]['url'] == 'https://fakeurl.com'
        
    def test_get_card_expense_attach_receipt_action(self):
        FAKE_EXPENSE_ID = 1
        card_expense_attach_receipt_action = messages.get_card_expense_attach_receipt_action(FAKE_EXPENSE_ID)
        assert card_expense_attach_receipt_action['value'] == FAKE_EXPENSE_ID

    def test_get_card_expense_section_blocks(self):
        FAKE_EXPENSE, FAKE_TITLE_TEXT = expense_data['FAKE_EXPENSE'], 'fake-title-text'
        card_expense_section_block = messages.get_card_expense_section_blocks(FAKE_EXPENSE, FAKE_TITLE_TEXT)
        assert card_expense_section_block[0]['block_id'] == 'expense_id.fake-id-123'
        assert card_expense_section_block[1]['fields'][0]['text'] == 'Date of Spend:\n *August 12, 2011*'
        assert card_expense_section_block[2]['fields'][0]['text'] == 'Card No.:\n *Ending 4567 (VISA)*'

    def test_get_expense_mandatory_receipt_missing_notification(self):
        FAKE_EXPENSE, FAKE_EXPENSE_URL = expense_data['FAKE_EXPENSE'], 'https://fakeurl.com'
        card_expense_section_block, title_text = messages.get_expense_mandatory_receipt_missing_notification(FAKE_EXPENSE, FAKE_EXPENSE_URL)
        display_amount = slack_utils.get_display_amount(FAKE_EXPENSE['amount'], FAKE_EXPENSE['currency'])
        assert title_text == f':credit_card: A card expense of *{display_amount}* requires a :receipt: receipt. Please reply with a photo of your receipt in this thread!'
        assert card_expense_section_block[0]['text']['text'] == ":credit_card: A card expense of *$100.00* requires a :receipt: receipt. Please reply with a photo of your receipt in this thread!"
        assert card_expense_section_block[1]['fields'][0]['text'] == 'Date of Spend:\n *August 12, 2011*'
        assert card_expense_section_block[1]['fields'][1]['text'] == "Receipt:\n :x: *Missing*"
        assert card_expense_section_block[2]['fields'][0]['text'] == "Card No.:\n *Ending 4567 (VISA)*"
        assert card_expense_section_block[3]['elements'][1]['value'] == "fake-id-123"
        assert card_expense_section_block[2]['fields'][1]['text'] == "Merchant:\n *Uber*"