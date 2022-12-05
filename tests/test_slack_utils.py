from fyle_slack_app.slack import utils
from slack_sdk.web import WebClient
from babel.numbers import get_currency_precision
import pytest

class TestSlackUtils:

    def test_get_slack_user_dm_channel_id(self, mocker):
        mock_slack_user_dm_channel = {
            'ok': True,
            'channel':{
                'id':[1, 2, 3]
            }
        }
        mocker.patch('slack_sdk.web.WebClient.conversations_open', return_value = mock_slack_user_dm_channel)
        slack_client, user_id = WebClient(), 'fake-user-id'
        dm_channel_ids = utils.get_slack_user_dm_channel_id(slack_client, user_id)
        assert dm_channel_ids == mock_slack_user_dm_channel['channel']['id']

    def test_round_amount(self):
        amount, currency = None, None
        try:
            utils.round_amount(amount, currency)
        except ValueError:
            assert pytest.raises(ValueError)

        amount, currency = 1000.23453, None
        try:
            utils.round_amount(amount, currency)
        except ValueError as msg:
            assert pytest.raises(ValueError)

        amount, currency = None, 'USD'
        try:
            utils.round_amount(amount, currency)
        except ValueError as msg:
            assert pytest.raises(ValueError)

        amount, currency = 100.5678, 'USD'
        rounded_amount = utils.round_amount(amount, currency)
        assert rounded_amount == round(amount + 1e-9, get_currency_precision(currency))

    def test_get_display_amount(self):
        assert "₹100,000.00" == str(utils.get_display_amount("100,000", 'INR'))
        assert "$100,000.00" == str(utils.get_display_amount("100,000", 'USD'))
