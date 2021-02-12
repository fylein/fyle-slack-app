import json
import base64


def fyle_authorization(request):
    code = request.GET.get('code')
    state = request.GET.get('state')

    decoded_state = base64.urlsafe_b64decode(state.encode())
    state_json = json.loads(decoded_state.decode())

    pass