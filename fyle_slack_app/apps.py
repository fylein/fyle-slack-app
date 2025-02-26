from django.apps import AppConfig


class FyleSlackAppConfig(AppConfig):
    name = 'apps,fyle_slack_app'

    def ready(self) -> None:
        super().ready()
        # pylint: disable=unused-import
        # pylint: disable=import-outside-toplevel
        import fyle_slack_app.signals
