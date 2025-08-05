from django.http import JsonResponse


def ready(request):
    from fyle_slack_app.models.users import User
    User.objects.first()

    return JsonResponse({'message': 'slack app service is ready'}, status=200)
