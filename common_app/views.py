# coding: utf-8
from __future__ import absolute_import, print_function

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from common_dibbs.clients.ar_client.apis.sites_api import SitesApi
from common_dibbs.clients.rm_client.apis.credentials_api import CredentialsApi
from common_dibbs.clients.rm_client.apis.users_api import UsersApi
from common_dibbs.django import relay_swagger


@login_required
def credentials(request, message_success=None):
    # Create a client for Credentials
    credentials_client = CredentialsApi()
    credentials_client.api_client.host = settings.DIBBS['urls']['rm']
    relay_swagger(credentials_client, request)

    creds = credentials_client.credentials_get()

    return render(request, "credentials.html", {"credentials_list": creds,
                                                "message_success": message_success})


@login_required
def credentials_form(request, message_error=None):
    # Create a client for Users
    users_client = UsersApi()
    users_client.api_client.host = settings.DIBBS['urls']['rm']
    relay_swagger(users_client, request)

    # Create a client for Sites
    sites_client = SitesApi()
    sites_client.api_client.host = settings.DIBBS['urls']['ar']
    relay_swagger(sites_client, request)

    # TODO: Remove hardcoded ID when central authentication system implemented
    public_key = users_client.rsa_public_key_id_get(id=1).public_key
    public_key = public_key.replace('\n', '\\n')

    providers = sites_client.sites_get()

    return render(request, "credentials_form.html", {"service_providers": providers,
                                                     "public_key": public_key,
                                                     "message_error": message_error})


@login_required
def credentials_post(request):
    service_provider = request.POST.get('service_provider')
    encrypted_content = request.POST.get('encrypted_content')

    request_data = {
        "site_name": service_provider,
        "credentials": encrypted_content,
        "name": "%s_%s" % (request.user.username, service_provider)
    }

    # Create a client for Credentials
    credentials_client = CredentialsApi()
    credentials_client.api_client.host = settings.DIBBS['urls']['rm']
    relay_swagger(credentials_client, request)

    try:
        ret = credentials_client.credentials_post(data=request_data)
        site_name = ret.site_name
        return credentials(request, message_success="Successfully created credentials for service \"" +
                                                    str(site_name) + "\".")
    except Exception as e:
        return credentials_form(request, message_error="Error creating the credentials: " + str(e))
