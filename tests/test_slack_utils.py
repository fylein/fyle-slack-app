from fyle_slack_app.slack import utils
from slack_sdk.web import WebClient
from babel.numbers import get_currency_precision
from fyle_slack_app.models import Team, User
from slack_sdk.errors import SlackApiError
import requests

import pytest
import mock

class TestSlackUtils:

    def test_get_slack_client(self, mocker):
        fake_team = mock.MagicMock(spec = Team)
        fake_team.bot_access_token = 'fake-access-token'
        TEAM_ID = 'fake-team-id'
        mocker.patch('fyle_slack_app.libs.utils.get_or_none', return_value = fake_team)
        mocker.patch('slack_sdk.web.WebClient', return_value = True)
        assert utils.get_slack_client(TEAM_ID)

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

    def test_get_user_display_name(self, mocker):
        MockWebClient = mock.Mock(spec = WebClient)
        slack_client = MockWebClient()
        user_details = {
            'email':'fakeemail@gmail.com',
            'full_name': 'Fake Name'
        }
        USER_ID = 'fake-user-id'
        slack_client.users_lookupByEmail.return_value = {
            'user':{
                'id':USER_ID
            }
        }
        user_display_name = f'<@{USER_ID}>'
        assert user_display_name == utils.get_user_display_name(slack_client, user_details)

    def test_get_file_content_from_slack(self, mocker):
        URL = 'https://www.google.com'
        bot_access_token = 'fake-bot-access-token' 
        response = mock.Mock(spec = requests.Response)
        response.status_code = 200
        response.content = 'content'
        mocker.patch('fyle_slack_app.libs.http.get', return_value = response)
        content = utils.get_file_content_from_slack(URL, bot_access_token)
        assert content == response.content

    def test_get_slack_latest_parent_message(self, mocker):
        mock_user = mock.Mock(spec=User)
        mock_user.slack_dm_channel_id = 'slack_dm_channel_id'
        MockWebClient = mock.Mock(spec = WebClient)
        slack_client = MockWebClient()
        slack_client.conversations_history.return_value = {
            'messages':['Message1']
        }
        parent_message =  utils.get_slack_latest_parent_message(mock_user, slack_client, 'thread_ts')
        assert parent_message == 'Message1'

    def test_send_slack_response_in_thread(self, mocker):
        MockWebClient = mock.Mock(spec = WebClient)
        slack_client = MockWebClient()
        mock_user = mock.Mock(spec=User)
        mock_user.slack_dm_channel_id = 'slack_dm_channel_id'
        slack_client.chat_postMessage.return_value = True
        assert utils.send_slack_response_in_thread(mock_user, slack_client, [], 'fake_thread_ts')

    def test_update_slack_parent_message(self, mocker):
        parent_message = {
            'blocks': [{'elements': [0, 1, 2]}],
            'ts':[]
        }
        MockWebClient = mock.Mock(spec = WebClient)
        slack_client = MockWebClient()
        mock_user = mock.Mock(spec=User)
        mock_user.slack_dm_channel_id = 'slack_dm_channel_id'
        slack_client.chat_update.return_value = True
        assert utils.update_slack_parent_message(mock_user, slack_client, parent_message, [], True, True) is None

