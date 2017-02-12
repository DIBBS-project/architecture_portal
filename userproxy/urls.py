# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

from django.conf.urls import include, url
from django.contrib import admin

from userproxy import views

urlpatterns = [
    url(r'^test$', views.user_data, name='home'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
]
