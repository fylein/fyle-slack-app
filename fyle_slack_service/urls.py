"""slack URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from fyle_slack_app.slack.authorization import views as slack_auth_views
from fyle_slack_app.slack.interactives import views as slack_interactive_views
from fyle_slack_app.slack.events import  views as slack_event_views
from fyle_slack_app.slack.commands import views as slack_command_views

from fyle_slack_app.fyle.authorization import views as fyle_auth_views
from fyle_slack_app.fyle.report_approvals import views as fyle_report_approval_views


urlpatterns = [
    path('admin/', admin.site.urls),

    # Slack routes
    path('slack/authorization', slack_auth_views.SlackAuthorization.as_view()),

    path('slack/direct_install', slack_auth_views.SlackDirectInstall.as_view()),

    # Fyle routes
    path('fyle/authorization', fyle_auth_views.FyleAuthorization.as_view()),

    path('fyle/schedule_report_polling', fyle_report_approval_views.FyleReportPolling.as_view()),

    # Slack interactive routes
    path('slack/interactives', slack_interactive_views.SlackInteractiveView.as_view()),

    path('slack/events', slack_event_views.SlackEventView.as_view()),

    path('slack/commands/<str:command>', slack_command_views.SlackCommandView.as_view())

]
