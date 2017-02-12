# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

from common_dibbs.names import AUTHORIZATION_HEADER as AUTH_HEADER


def configure_swagger(swagger_client, incoming_request):
    headers = {AUTH_HEADER: incoming_request.user.dibbs_user.token}
    swagger_client.api_client.default_headers.update(headers)
