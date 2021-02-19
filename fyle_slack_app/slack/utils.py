from slack_sdk import WebClient

from ..libs import assertions


def get_slack_user_dm_channel_id(slack_client: WebClient, user_id: str) -> str:
    slack_user_dm_channel_id = slack_client.conversations_open(users=[user_id])
    assertions.assert_good(slack_user_dm_channel_id['ok'] == True)
    return slack_user_dm_channel_id['channel']['id']