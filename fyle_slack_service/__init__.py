from django.http import JsonResponse

def ready(request):
    return JsonResponse({'message': 'slack app service is ready'}, status=200)


def traces_sampler(sampling_context):
    # avoiding ready APIs in performance tracing
    if sampling_context.get('wsgi_environ') is not None:
        if sampling_context['wsgi_environ']['PATH_INFO'] in ['/ready']:
            return 0

    return 0.2
