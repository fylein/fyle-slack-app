import mock

from django.test import RequestFactory
from django.conf import settings

from fyle_slack_app.slack.authorization.views import SlackAuthorization


@mock.patch('fyle_slack_app.slack.authorization.views.utils')
@mock.patch('fyle_slack_app.slack.authorization.views.Team')
@mock.patch('fyle_slack_app.slack.authorization.views.async_task')
@mock.patch('fyle_slack_app.slack.authorization.views.WebClient')
def test_slack_authorization(web_client, async_task, team, utils):
    request = RequestFactory().get('slack/authorization')
    request.GET = {
        'code': 'some-secret-code'
    }

    # Mocking slack sdk call's response
    web_client.return_value.oauth_v2_access.return_value = {
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

    team.objects.create.return_value = 'slack team'

    async_task.return_value = True

    # Calling the SlackAuthorization view for test
    view = SlackAuthorization.as_view()(request)

    # Checking the required methods have been called
    web_client.return_value.oauth_v2_access.assert_called()
    web_client.return_value.oauth_v2_access.assert_called_with(
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
