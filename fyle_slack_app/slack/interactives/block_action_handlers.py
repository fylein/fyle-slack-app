from typing import Callable, Dict
from slack_sdk.web.client import WebClient

from django.http.response import JsonResponse

from ...slack.utils import get_slack_user_dm_channel_id


class BlockActionHandler():

    def __init__(self) -> None:
        self._block_action_handlers = {
            'link_fyle_account': self.link_fyle_account
        }


    # Gets called when function with an action is not found
    def _handle_invalid_block_actions(self, slack_client: WebClient, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        user_dm_channel_id = get_slack_user_dm_channel_id(slack_client, user_id)
        slack_client.chat_postMessage(
            channel=user_dm_channel_id,
            text='Seems like something bad happened :zipper_mouth_face: \n Please try again'
        )
        return JsonResponse({}, status=200)


    # Handle all the block actions from slack
    def handle_block_actions(self, slack_client: WebClient, slack_payload: Dict, user_id: str, team_id: str) -> Callable:
        '''
            Check if any function is associated with the action
            If present handler will call the respective function
            If not present call `handle_invalid_block_actions` to send a prompt to user
        '''
        action_id = slack_payload['actions'][0]['action_id']

        handler = self._block_action_handlers.get(action_id, self._handle_invalid_block_actions)

        return handler(slack_client, slack_payload, user_id, team_id)


    # Define all the action handlers below this

    def link_fyle_account(self, slack_client: WebClient, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        # Empty function because slack still sends an interactive event on button click and expects a 200 response
        return JsonResponse({}, status=200)
