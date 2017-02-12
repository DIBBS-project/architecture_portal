# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
import requests

from .models import UserProfile


def _auth_user_exists(user, password):
    auth_response = requests.get(
        settings.DIBBS['urls']['cas'] + '/auth/tokens',
        headers={'Dibbs-Authorization': user.dibbs_user.token},
    )
    if auth_response.status_code == 200:
        return user

    # try to get new token
    auth_response = requests.post(
        settings.DIBBS['urls']['cas'] + '/auth/tokens',
        json={'username': user.username, 'password': password},
    )
    if auth_response.status_code != 200:
        # user now invalid?
        return None

    user.dibbs_user.token = auth_response.json()['token']
    user.dibbs_user.save()
    return user


def _auth_new_user(username, password):
    UserModel = get_user_model()
    # validate user/pass by getting token
    auth_response = requests.post(
        settings.DIBBS['urls']['cas'] + '/auth/tokens',
        json={'username': username, 'password': password},
    )
    if auth_response.status_code != 200:
        return None

    user = UserModel.objects.create(username=username)
    user.set_password(password)
    user.save()

    auth_data = auth_response.json()
    token = auth_data['token']

    user_profile = UserProfile.objects.create(user=user, token=token)

    return user


def authenticate_dibbs(username, password):
    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(username=username)
    except UserModel.DoesNotExist:
        print('new user')
        user = _auth_new_user(username, password)
    else:
        print('user found')
        user = authenticate(username=username, password=password) # hacky...
        if user is None:
            print('failed to authenticate')

            # password changed?
            return None
        new_user = _auth_user_exists(user, password)
    return authenticate(username=username, password=password)
