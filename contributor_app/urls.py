"""architecture_portal URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url

from contributor_app import views

urlpatterns = [
    url(r'^$', views.index, name='contributor_index'),
    url(r'^operations/$', views.operations, name='contributor_operations'),
    url(r'^operations/(?P<operation_id>[0-9]+)/$',
        views.operation_detail, name='contributor_operation_detail'),
    url(r'^appliances/$', views.appliances, name='contributor_appliances'),
    url(r'^operation_form/$', views.operation_form, name='contributor_operation_form'),
    url(r'^operation_post/$', views.operation_post, name='contributor_operation_post'),
    url(r'^appliance_form/$', views.appliance_form, name='contributor_appliance_form'),
    url(r'^appliance_post/$', views.appliance_post, name='contributor_appliance_post'),
    url(r'^appliance_implementations/(?P<appliance_impl_name>.+)/$',
        views.appliance_implementation_detail, name='contributor_appliance_implementation_detail'),
    url(r'^appliance_implementation_form/$',
        views.appliance_implementation_form, name='contributor_appliance_implementation_form'),
    url(r'^appliance_implementation_post/$',
        views.appliance_implementation_post, name='contributor_appliance_implementation_post'),
]
