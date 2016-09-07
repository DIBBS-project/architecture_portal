from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions
from settings import Settings
from django.shortcuts import redirect
import requests
import uuid
from django.shortcuts import render


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
            user.username = "jpastor"

        return {
            "user": user,
            "token": result.token
        }

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class CentralAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        username = request.META.get('X_USERNAME')
        password = request.META.get('X_PASSWORD')
        session_key = request.session.session_key

        auth_backend = ClientAuthenticationBackend()

        # Check if the current session has already been authenticated by the CAS: authentication is successful
        authentication_resp = auth_backend.authenticate(username, password, session_key)
        if authentication_resp["user"] is not None:
            return (authentication_resp["user"], None)

        # Do a web redirection to the CAS service
        redirect_url = "http://%s%s" % (request.META.get('HTTP_HOST'), request.GET["next"])
        cas_service_target_url = "%s" % (Settings().central_authentication_service_url, )

        data = {
            "session_key": session_key,
            "redirect_url": redirect_url,
            "cas_service_target_url": cas_service_target_url
        }

        # # (a) Redirection via a GET request
        # response = redirect(cas_service_target_url, (authentication_resp["token"]))
        # return response

        # (b) Redirection via a form
        return render(request, "redirect.html", data)


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

        # # (a) Redirection via a GET request
        # response = redirect(cas_service_target_url, (authentication_resp["token"]))
        # return response

        # (b) Redirection via a form
        return render(request, "redirect.html", data)
        # return

LOGGED_USERS = {

}


# def login(request):
#     return CentralAuthentication().authenticate(request)
#
#
# def logout(request):
#     return True
