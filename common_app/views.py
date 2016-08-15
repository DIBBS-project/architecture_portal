from django.shortcuts import render


def credentials(request, message_success=None):
    from rp_client.apis.credentials_api import CredentialsApi

    creds = CredentialsApi().credentials_get()

    return render(request, "credentials.html", {"credentials_list": creds,
                                                "message_success": message_success})


def credentials_form(request, message_error=None):
    from ar_client.apis.sites_api import SitesApi
    from rp_client.apis.users_api import UsersApi
    import string

    # TODO: Remove hardcoded ID when central authentication system implemented
    public_key = UsersApi().rsa_public_key_id_get(id=1).public_key
    public_key = string.replace(public_key, '\n', '\\n')

    providers = SitesApi().sites_get()

    return render(request, "credentials_form.html", {"service_providers": providers,
                                                     "public_key": public_key,
                                                     "message_error": message_error})


def credentials_post(request):
    from rp_client.apis.credentials_api import CredentialsApi
    from rp_client.configure import configure_auth_basic

    service_provider = request.POST.get('service_provider')
    encrypted_content = request.POST.get('encrypted_content')

    request_data = {
        "site_name": service_provider,
        "credentials": encrypted_content
    }

    configure_auth_basic("admin", "pass")
    try:
        ret = CredentialsApi().credentials_post(data=request_data)
        site_name = ret.site_name
        return credentials(request, message_success="Successfully created credentials for service \"" +
                                                    str(site_name) + "\".")
    except Exception as e:
        return credentials_form(request, message_error="Error creating the credentials: " + str(e))
