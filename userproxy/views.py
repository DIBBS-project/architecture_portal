# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

import json

from django.conf import settings
from django.contrib import auth
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect
# import requests

# from .models import UserProfile
from .auth import authenticate_dibbs


def _user_request_data(request):
    return HttpResponse(json.dumps({
        'user': str(request.user),
        'is_anonymous': bool(request.user.is_anonymous()),
        'is_active': bool(request.user.is_active),
        'is_authenticated': bool(request.user.is_authenticated()),
    }, indent=4), content_type='application/json')


def login(request):
    if request.method == 'GET':
        return render(request, 'userproxy/login.html')
    elif request.method != 'POST':
        raise HttpResponseNotAllowed()

    auth.logout(request)
    user = authenticate_dibbs(
        username=request.POST['username'],
        password=request.POST['password'],
    )
    if user is not None:
        if user.is_active:
            auth.login(request, user)
            return redirect('/')

    return render(request, 'userproxy/login.html', context={
        'error': 'Invalid credentials.',
    })


def logout(request):
    auth.logout(request)
    return HttpResponse('200 OK')


def user_data(request):
    return _user_request_data(request)
