from django.http import JsonResponse

def ready(request):
    return JsonResponse({'message': 'slack app service is ready'}, status=200)
