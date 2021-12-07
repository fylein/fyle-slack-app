python manage.py migrate
python manage.py createcachetable --database cache
gunicorn -c gunicorn_config.py fyle_slack_service.wsgi -b 0.0.0.0:8000