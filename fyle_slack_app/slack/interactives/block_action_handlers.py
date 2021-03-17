from django.http.response import JsonResponse

from django_q.tasks import async_task

from ...slack.utils import get_report_employee_display_name, get_slack_user_dm_channel_id
from ...libs import utils, assertions
from ...fyle.report_approvals.views import FyleReportApproval
from ...models import User
from ..ui.report_approvals import messages as report_approval_messages


class BlockActionHandler():

    _block_action_handlers = {}

    # Maps action_id with it's respective function
    def _initialize_block_action_handlers(self):
        self._block_action_handlers = {
            'link_fyle_account': self.link_fyle_account,
            'report_review_in_fyle': self.review_report_in_fyle,
            'report_approve': self.report_approve
        }


    # Gets called when function with an action is not found
    def _handle_invalid_block_actions(self, slack_client, slack_payload, user_id, team_id):
        user_dm_channel_id = get_slack_user_dm_channel_id(slack_client, user_id)
        slack_client.chat_postMessage(
            channel=user_dm_channel_id,
            text='Seems like something bad happened :zipper_mouth_face: \n Please try again'
        )
        return JsonResponse({}, status=200)


    # Handle all the block actions from slack
    def handle_block_actions(self, slack_client, slack_payload, user_id, team_id):
        '''
            Check if any function is associated with the action
            If present handler will call the respective function
            If not present call `handle_invalid_block_actions` to send a prompt to user
        '''

        # Initialize handlers
        self._initialize_block_action_handlers()

        action_id = slack_payload['actions'][0]['action_id']

        handler = self._block_action_handlers.get(action_id, self._handle_invalid_block_actions)

        return handler(slack_client, slack_payload, user_id, team_id)


    # Define all the action handlers below this

    def link_fyle_account(self, slack_client, slack_payload, user_id, team_id):
        # Empty function because slack still sends an interactive event on button click and expects a 200 response
        return JsonResponse({}, status=200)


    def review_report_in_fyle(self, slack_client, slack_payload, user_id, team_id):
        # Empty function because slack still sends an interactive event on button click and expects a 200 response
        return JsonResponse({}, status=200)


    def report_approve(self, slack_client, slack_payload, user_id, team_id):
        report_id = slack_payload['actions'][0]['value']
        message_ts = slack_payload['message']['ts']

        # pylint: disable=line-too-long
        async_task('fyle_slack_app.slack.interactives.tasks.process_report_approval', report_id, user_id, team_id, message_ts)

        # user = utils.get_or_none(User, slack_user_id=user_id)
        # assertions.assert_found(user, 'Approver not found')

        # query_params = {
        #     'id': 'eq.{}'.format(report_id),
        #     # Mandatory query params required by sdk
        #     'limit': 1,
        #     'offset': 0,
        #     'order': 'submitted_at.desc'
        # }
        # approver_report = FyleReportApproval.get_approver_reports(user, query_params)['data'][0]
        # # approver_report = FyleReportApproval.get_approver_report_by_id(user, report_id)['data']

        # report_approved_states = ['PAYMENT_PENDING', 'APPROVED', 'PAYMENT_PROCESSING', 'PAID']

        # is_report_approved = False
        # is_report_approvable = True

        # if approver_report['state'] == 'APPROVER_INQUIRY':
        #     is_report_approvable = False
        #     message = 'This report can\'t be approved as it is sent back to the employee :x:'

        # if approver_report['state'] in report_approved_states and is_report_approvable is True:
        #     is_report_approved = True
        #     message = 'This report is already approved :white_check_mark:'

        # if is_report_approved is False and is_report_approvable is True:

        #     for approver in approver_report['approvals']:

        #         if approver['approver_id'] == user.fyle_employee_id:

        #             if approver['state'] == 'APPROVAL_DONE':
        #                 is_report_approved = True
        #                 message = 'This report is already approved by you :white_check_mark:'

        #             if approver['state'] == 'APPROVAL_DISABLED':
        #                 is_report_approvable = False
        #                 message = 'Your approval is disabled on this report :x:'

        # employee_display_name = get_report_employee_display_name(slack_client, approver_report['employee'])

        # report_section_block = report_approval_messages.get_report_section_blocks(
        #     approver_report,
        #     employee_display_name
        # )

        # if is_report_approvable is False or is_report_approved is True:
        #     message_section = {
        #         'type': 'section',
        #         'text': {
        #             'type': 'mrkdwn',
        #             'text': message
        #         }
        #     }

        #     report_section_block.append(message_section)

        #     slack_client.chat_update(
        #         channel=user.slack_dm_channel_id,
        #         blocks=report_section_block,
        #         ts=slack_payload['message']['ts']
        #     )

        return JsonResponse({}, status=200)
