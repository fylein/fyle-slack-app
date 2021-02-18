from typing import Dict
from slack_sdk.web.client import WebClient

from django.http.response import JsonResponse


class BlockActionHandler():

    def link_fyle_account(self, slack_client: WebClient, slack_payload: Dict, user_id: str, team_id: str) -> JsonResponse:
        # Empty function because slack still sends an interactive event on button click and expects a 200 response
        return JsonResponse({}, status=200)
