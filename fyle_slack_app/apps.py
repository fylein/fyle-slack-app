from django.apps import AppConfig

class FyleSlackAppConfig(AppConfig):
    name = 'fyle_slack_app'

    def ready(self):
        super().ready()

        # NOTE: Need to import like this because django throws an error
        # if we import any django app related module before `ready()` function is completed
        # i.e. here `super.ready()`
        from .fyle.report_approvals.tasks import schedule_report_approval_polling

        # Schedule report polling background task
        schedule_report_approval_polling()
