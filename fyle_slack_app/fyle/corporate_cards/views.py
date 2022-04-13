from typing import Dict

from fyle.platform.platform import Platform

from fyle_slack_app.models.users import User
from fyle_slack_app.fyle import utils as fyle_utils

class FyleCorporateCards:

    connection: Platform = None

    def __init__(self, user: User) -> None:
        self.connection = fyle_utils.get_fyle_sdk_connection(user.fyle_refresh_token)


    def get_corporate_card_by_id(self, query_params: Dict) -> Dict:
        corporate_card = self.connection.v1beta.spender.corporate_cards.list(query_params=query_params)
        return corporate_card

    # comment
