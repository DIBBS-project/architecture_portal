from django.contrib.auth.models import User
from django.shortcuts import render

from settings import Settings


class ClientAuthenticationBackend(object):
    def authenticate(self, username=None, password=None, session_key=None):
        from cas_client.apis.authentication_api import AuthenticationApi

        # Create a client for Authentication
        operations_client = AuthenticationApi()
        operations_client.api_client.host = "%s" % (Settings().central_authentication_service_url,)

        result = operations_client.authenticate_post(**{
            "username": username,
            "password": password,
            "session_key": session_key,
        })

        user = None
        if result.response:
            user = User()
            user.username = result.username

        return {
            "user": user,
            "token": result.token
        }


class CentralAuthenticationMiddleware(object):
    def process_request(self, request):
        username = request.META.get('X_USERNAME')
        password = request.META.get('X_PASSWORD')
        session_key = request.session.session_key

        auth_backend = ClientAuthenticationBackend()

        # Check if the current session has already been authenticated by the CAS: authentication is successful
        authentication_resp = auth_backend.authenticate(username, password, session_key)

        if authentication_resp["user"] is not None and authentication_resp["user"].username not in ["", "anonymous"]:
            request.user = authentication_resp["user"]
            return

        # Do a web redirection to the CAS service
        redirect_url = "http://%s%s" % (request.META.get('HTTP_HOST'), request.path)
        cas_service_target_url = "%s" % (Settings().central_authentication_service_url, )

        data = {
            "session_key": session_key,
            "redirect_url": redirect_url,
            "cas_service_target_url": cas_service_target_url
        }

        # Redirection via a form
        return render(request, "redirect_form.html", data)

LOGGED_USERS = {

}
