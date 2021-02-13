import json
import base64

from django.http.response import JsonResponse
from django.views import View


class FyleAuthorization(View):

    def get(self, request) -> JsonResponse:
        code = request.GET.get('code')
        state = request.GET.get('state')

        decoded_state = base64.urlsafe_b64decode(state.encode())
        state_json = json.loads(decoded_state.decode())
        pass