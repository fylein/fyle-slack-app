import mock

from django.http import HttpResponseRedirect
from django.test import RequestFactory
from django.conf import settings

from fyle_slack_app.models import Team, User
from fyle_slack_app.slack.utils import encode_state
from fyle_slack_app.slack.authorization.views import SlackAuthorization
from fyle_slack_app.fyle.authorization.views import FyleAuthorization


@mock.patch('fyle_slack_app.slack.authorization.views.utils')
@mock.patch('fyle_slack_app.slack.authorization.views.Team')
@mock.patch('fyle_slack_app.slack.authorization.views.async_task')
@mock.patch('fyle_slack_app.slack.authorization.views.WebClient')
def test_slack_authorization(slack_client, async_task, team, utils):

    # Create a request object to send to view for testing
    request = RequestFactory().get('slack/authorization')
    request.GET = {
        'code': 'some-secret-code'
    }

    # Mocking slack sdk call's response
    slack_client.return_value.oauth_v2_access.return_value = {
        'ok': True,
        'team': {
            'id': 'TA12345',
            'name': 'Test Team'
        },
        'bot_user_id': 'bot-abcd-12345',
        'access_token': 'secret-token'
    }

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
        code='some-secret-code'
    )

    utils.get_or_none.assert_called_once()
    utils.get_or_none.assert_called_with(team, id='TA12345')

    team.objects.create.assert_called_once()
    team.objects.create.assert_called_with(
        id='TA12345',
        name='Test Team',
        bot_user_id='bot-abcd-12345',
        bot_access_token='secret-token'
    )

    async_task.assert_called_once()
    async_task.assert_called_with(
        'fyle_slack_app.slack.authorization.tasks.broadcast_installation_message',
        'TA12345'
    )


@mock.patch('fyle_slack_app.fyle.authorization.views.utils')
@mock.patch('fyle_slack_app.fyle.authorization.views.get_slack_user_dm_channel_id')
@mock.patch('fyle_slack_app.fyle.authorization.views.WebClient')
@mock.patch.object(FyleAuthorization, 'create_user')
@mock.patch.object(FyleAuthorization, 'send_post_authorization_message')
@mock.patch.object(FyleAuthorization, 'get_fyle_refresh_token')
def test_fyle_authorization(get_fyle_refresh_token, send_post_authorization_message, create_user, slack_client, slack_user_dm_channel_id, utils):

    state_params = {
        'team_id': 'T12345',
        'user_id': 'U12345'
    }

    b64_encoded_state = encode_state(state_params)

    # Create a request object to send to view for testing
    request = RequestFactory().get('fyle/authorization')
    request.GET = {
        'code': 'secret-fyle-code',
        'state': b64_encoded_state
    }

    # Returns next value each time get_or_none is called
    # in function which is to be tested
    mock_team = mock.Mock(spec=Team)
    utils.get_or_none.side_effect = [mock_team, None]

    slack_user_dm_channel_id.return_value = 'UDM12345'

    # Mock FyleAuthorization class methods
    get_fyle_refresh_token.return_value = 'fyle-refresh-token'
    create_user.return_value = mock.Mock(spec=User)
    send_post_authorization_message.return_value = True

    # Call function to test
    response = FyleAuthorization.as_view()(request)

    # Checking response type
    assert isinstance(response, HttpResponseRedirect)

    # Checking the required methods have been called
    get_fyle_refresh_token.assert_called()
    get_fyle_refresh_token.assert_called_with('secret-fyle-code')

    create_user.assert_called()
    create_user.assert_called_with(slack_client(), mock_team, state_params['user_id'], 'UDM12345', 'fyle-refresh-token')

    send_post_authorization_message.assert_called()
    send_post_authorization_message.assert_called_with(slack_client(), 'UDM12345')

    # Check is get_or_none function has been called twice
    assert utils.get_or_none.call_count == 2

    # We call get_or_none twice in view to be tested
    # This check if the parameters passed in each call are correct or not
    expected_calls = [
        mock.call(Team, id=state_params['team_id']),
        mock.call(User, slack_user_id=state_params['user_id'])
    ]

    utils.get_or_none.assert_has_calls(expected_calls)
