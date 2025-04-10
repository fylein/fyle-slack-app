from django.http import JsonResponse
from fyle_slack_app.models.users import User


def ready(request):
    User.objects.first()

    return JsonResponse({'message': 'slack app service is ready'}, status=200)
