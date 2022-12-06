import mock

from django.http import HttpResponseRedirect
from django.test import RequestFactory
from django.conf import settings

from fyle_slack_app.models import Team, User
from fyle_slack_app.libs.utils import encode_state, decode_state
from fyle_slack_app.slack.authorization.views import SlackAuthorization
from fyle_slack_app.fyle.authorization.views import FyleAuthorization
from slack_sdk.web.client import WebClient

@mock.patch('fyle_slack_app.slack.authorization.views.utils')
@mock.patch('fyle_slack_app.slack.authorization.views.Team')
@mock.patch('fyle_slack_app.slack.authorization.views.async_task')
@mock.patch('fyle_slack_app.slack.authorization.views.WebClient')
@mock.patch.object(SlackAuthorization, 'track_installation')
def test_slack_authorization(track_installation, slack_client, async_task, team, utils):

    # Create a request object to send to view for testing
    request = RequestFactory().get('slack/authorization')
    slack_secret_code = 'some-secret-code'
    request.GET = {
        'code': slack_secret_code
    }

    mock_oauth_v2_access_response = {
        'ok': True,
        'team': {
            'id': 'TA12345',
            'name': 'Test Team'
        },
        'authed_user': {
            'id': 'U12345'
        },
        'bot_user_id': 'bot-abcd-12345',
        'access_token': 'secret-token'
    }

    # Mocking slack sdk call's response
    slack_client.return_value.oauth_v2_access.return_value = mock_oauth_v2_access_response

    # Condition where slack team is not registered/created in our DB
    utils.get_or_none.return_value = None

    mock_team = mock.Mock(spec=Team)
    team.objects.create.return_value = mock_team

    async_task.return_value = True

    # Calling the SlackAuthorization view for test
    response = SlackAuthorization.as_view()(request)

    # Checking response type
    assert isinstance(response, HttpResponseRedirect)

    # Checking the required methods have been called
    slack_client.return_value.oauth_v2_access.assert_called()
    slack_client.return_value.oauth_v2_access.assert_called_with(
        client_id=settings.SLACK_CLIENT_ID,
        client_secret=settings.SLACK_CLIENT_SECRET,
        code=slack_secret_code
    )

    utils.get_or_none.assert_called_once()
    utils.get_or_none.assert_called_with(team, id=mock_oauth_v2_access_response['team']['id'])

    team.objects.create.assert_called_once()
    team.objects.create.assert_called_with(
        id=mock_oauth_v2_access_response['team']['id'],
        name=mock_oauth_v2_access_response['team']['name'],
        bot_user_id=mock_oauth_v2_access_response['bot_user_id'],
        bot_access_token=mock_oauth_v2_access_response['access_token']
    )

    async_task.assert_called_once()
    async_task.assert_called_with(
        'fyle_slack_app.slack.authorization.tasks.broadcast_installation_message',
        mock_oauth_v2_access_response['team']['id']
    )

    track_installation.assert_called_once()
    track_installation.assert_called_with(mock_oauth_v2_access_response['authed_user']['id'], mock_team, slack_client())


@mock.patch('fyle_slack_app.fyle.authorization.views.utils')
@mock.patch('fyle_slack_app.fyle.authorization.views.fyle_utils')
@mock.patch('fyle_slack_app.slack.utils.get_slack_user_dm_channel_id')
@mock.patch('fyle_slack_app.fyle.authorization.views.WebClient')
@mock.patch('fyle_slack_app.fyle.authorization.views.transaction')
@mock.patch.object(FyleAuthorization, 'create_user')
@mock.patch.object(FyleAuthorization, 'send_post_authorization_message')
@mock.patch.object(FyleAuthorization, 'track_fyle_authorization')
@mock.patch.object(FyleAuthorization, 'create_notification_subscription')
def test_fyle_authorization(create_notification_subscription, track_fyle_authorization, send_post_authorization_message, create_user, transaction, slack_client, slack_user_dm_channel_id, fyle_utils, utils, mock_fyle):

    state_params = {
        'team_id': 'T12345',
        'user_id': 'U12345'
    }

    b64_encoded_state = encode_state(state_params)

    # Create a request object to send to view for testing
    request = RequestFactory().get('fyle/authorization')
    mock_fyle_secret_code = 'secret-fyle-code'
    request.GET = {
        'code': mock_fyle_secret_code,
        'state': b64_encoded_state
    }

    # Returns next value each time get_or_none is called
    # in function which is to be tested
    mock_team = mock.Mock(spec=Team)
    utils.get_or_none.side_effect = [mock_team, None, None]

    utils.decode_state = decode_state

    mock_slack_user_dm_channel_id = 'UDM12345'
    slack_user_dm_channel_id.return_value = mock_slack_user_dm_channel_id

    # Mocking django transaction block
    transaction.atomic.return_value.__enter__.return_value = True

    # Mock Fyle utils methods
    mock_fyle_refresh_token = 'fyle-refresh-token'
    fyle_utils.get_fyle_refresh_token.return_value = mock_fyle_refresh_token

    mock_fyle_profile = mock_fyle.spender.my_profile.get()['data']
    fyle_utils.get_fyle_profile.return_value = mock_fyle_profile

    mock_user = mock.Mock(spec=User)
    create_user.return_value = mock_user
    send_post_authorization_message.return_value = True

    create_notification_subscription.return_value = None

    # Call function to test
    response = FyleAuthorization.as_view()(request)

    # Checking response type
    assert isinstance(response, HttpResponseRedirect)

    # Checking the required methods have been called
    fyle_utils.get_fyle_refresh_token.assert_called_once()
    fyle_utils.get_fyle_refresh_token.assert_called_with(mock_fyle_secret_code)

    fyle_utils.get_fyle_profile.assert_called_once()
    fyle_utils.get_fyle_profile.assert_called_once_with(mock_fyle_refresh_token)

    create_user.assert_called()
    create_user.assert_called_with(slack_client(), mock_team, state_params['user_id'], 'UDM12345', mock_fyle_refresh_token, mock_fyle_profile)

    send_post_authorization_message.assert_called_once()
    send_post_authorization_message.assert_called_with(slack_client(), mock_slack_user_dm_channel_id)

    # Check is get_or_none function has been called thrice
    assert utils.get_or_none.call_count == 3

    # We call get_or_none thrice in view to be tested
    # This check if the parameters passed in each call are correct or not
    expected_calls = [
        mock.call(Team, id=state_params['team_id']),
        mock.call(User, slack_user_id=state_params['user_id']),
        mock.call(User, fyle_user_id=mock_fyle_profile['user_id'])
    ]

    utils.get_or_none.assert_has_calls(expected_calls)

    track_fyle_authorization.assert_called_once()
    track_fyle_authorization.assert_called_with(mock_user, mock_fyle_profile)

@mock.patch('fyle_slack_app.fyle.authorization.views.utils')
@mock.patch('fyle_slack_app.fyle.authorization.views.fyle_utils')
@mock.patch('fyle_slack_app.slack.utils.get_slack_user_dm_channel_id')
@mock.patch('fyle_slack_app.fyle.authorization.views.WebClient')
@mock.patch('fyle_slack_app.fyle.authorization.views.transaction')
@mock.patch.object(FyleAuthorization, 'create_user')
def test_fyle_authorization2(create_user, transaction, slack_client, slack_user_dm_channel_id, fyle_utils, utils, mock_fyle):

    state_params = {
        'team_id': 'T12345',
        'user_id': 'U12345'
    }

    b64_encoded_state = encode_state(state_params)

    # Create a request object to send to view for testing
    request = RequestFactory().get('fyle/authorization')
    mock_fyle_secret_code = 'secret-fyle-code'
    request.GET = {
        'code': mock_fyle_secret_code,
        'state': b64_encoded_state,
        'error': True
    }

    # Returns next value each time get_or_none is called
    # in function which is to be tested
    mock_team = mock.Mock(spec=Team)
    utils.get_or_none.side_effect = [mock_team, None, None]

    utils.decode_state = decode_state

    mock_slack_user_dm_channel_id = 'UDM12345'
    slack_user_dm_channel_id.return_value = mock_slack_user_dm_channel_id

    # Mocking django transaction block
    transaction.atomic.return_value.__enter__.return_value = True

    # Mock Fyle utils methods
    mock_fyle_refresh_token = 'fyle-refresh-token'
    fyle_utils.get_fyle_refresh_token.return_value = mock_fyle_refresh_token

    mock_fyle_profile = mock_fyle.spender.my_profile.get()['data']
    fyle_utils.get_fyle_profile.return_value = mock_fyle_profile

    mock_user = mock.Mock(spec=User)
    create_user.return_value = mock_user

    # Call function to test
    response = FyleAuthorization.as_view()(request)

    # Checking response type
    assert isinstance(response, HttpResponseRedirect)
