from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions
from settings import Settings


class ClientAuthBackend(object):
    def authenticate(self, username=None, password=None):
        from cas_client.apis.authentication_api import AuthenticationApi

        # Create a client for Authentication
        operations_client = AuthenticationApi()
        operations_client.api_client.host = "%s" % (Settings().central_authentication_service_url,)

        result = operations_client.authenticate_post({
            "username": username,
            "password": password
        })

        return None

    def get_user(self, user_id):
            return None


class ExampleAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        username = request.META.get('X_USERNAME') # get the username request header
        if not username: # no username passed in request headers
            return None # authentication did not succeed

        try:
            user = User.objects.get(username=username) # get the user
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('No such user') # raise exception if user does not exist

        return (user, None) # authentication successful