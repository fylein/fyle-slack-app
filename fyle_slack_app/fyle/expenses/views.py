from typing import Dict

from fyle.platform.platform import Platform

from fyle_slack_app.fyle.utils import get_fyle_sdk_connection
from fyle_slack_app.models.users import User


class FyleExpense:

    connection: Platform = None

    def __init__(self, user: User) -> None:
        self.connection = get_fyle_sdk_connection(user.fyle_refresh_token)


    def get_expense_fields(self, query_params: Dict) -> Dict:
        expense_fields = self.connection.v1.fyler.expense_fields.list(query_params=query_params)
        return expense_fields


    def get_default_expense_fields(self) -> Dict:
        default_expense_fields_query_params = {
            'offset': 0,
            'limit': '20',
            'order': 'created_at.desc',
            'column_name': 'in.(purpose, txn_dt, vendor_id, cost_center_id, project_id)',
            'is_enabled': 'eq.{}'.format(True),
            'is_custom': 'eq.{}'.format(False),
            'is_mandatory': 'eq.{}'.format(True)
        }

        default_expense_fields = self.get_expense_fields(default_expense_fields_query_params)

        return default_expense_fields


    def get_categories(self, query_params: Dict) -> Dict:
        categories = self.connection.v1.fyler.categories.list(query_params=query_params)
        return categories


    def get_projects(self, query_params: Dict) -> Dict:
        projects = self.connection.v1.fyler.projects.list(query_params=query_params)
        return projects


    @staticmethod
    def get_currencies():
        return ['ADP','AED','AFA','ALL','AMD','ANG','AOA','ARS','ATS','AUD','AWG','AZM','BAM','BBD','BDT','BEF','BGL','BGN','BHD','BIF','BMD','BND','BOB','BOV','BRL','BSD','BTN','BWP','BYB','BZD','CAD','CDF','CHF','CLF','CLP','CNY','COP','CRC','CUP','CVE','CYP','CZK','DEM','DJF','DKK','DOP','DZD','ECS','ECV','EEK','EGP','ERN','ESP','ETB','EUR','FIM','FJD','FKP','FRF','GBP','GEL','GHC','GIP','GMD','GNF','GRD','GTQ','GWP','GYD','HKD','HNL','HRK','HTG','HUF','IDE','IDR','IEP','ILS','INR','IQD','IRR','ISK','ITL','JMD','JOD','JPY','KES','KGS','KHR','KMF','KPW','KRW','KWD','KYD','KZT','LAK','LBP','LKR','LRD','LSL','LTL','LUF','LVL','LYD','MAD','MDL','MGF','MKD','MMK','MNT','MOP','MRO','MTL','MUR','MVR','MWK','MXN','MXV','MYR','MZM','NAD','NGN','NIO','NLG','NOK','NPR','NZD','OMR','PAB','PEN','PGK','PHP','PKR','PLN','PTE','PYG','QAR','ROL','RUB','RUR','RWF','RYR','SAR','SBD','SCR','SDP','SEK','SGD','SHP','SIT','SKK','SLL','SOS','SRG','STD','SVC','SYP','SZL','THB','TJR','TMM','TND','TOP','TPE','TRL','TTD','TWD','TZS','UAH','UGX','USD','USN','USS','UYU','UZS','VEB','VND','VUV','WST','XAF','XCD','XDR','XEU','XOF','XPF','YER','YUN','ZAR','ZMK','ZRN','ZWD']
