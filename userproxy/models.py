# coding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dibbs_user',
    )
    token = models.CharField(max_length=500)
