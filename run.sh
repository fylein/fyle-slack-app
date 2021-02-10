python manage.py migrate
gunicorn -c gunicorn_config.py fyle_slack_service.wsgi -b 0.0.0.0:8000