from django.apps import AppConfig

class FyleSlackAppConfig(AppConfig):
    name = 'fyle_slack_app'

    def ready(self) -> None:
        super().ready()

        # Schedule report polling background task

        # NOTE: Need to import like this because django throws an error
        # if we import any django app related module before `ready()` function is completed
        # i.e. here `super.ready()`
        from fyle_slack_app.fyle.report_approvals.tasks import schedule_report_approval_polling
        schedule_report_approval_polling()
