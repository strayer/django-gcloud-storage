"""test_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import url
from django.views.generic.base import TemplateView

from test_app.app import views

urlpatterns = [
    url(r'^upload$', views.TestUploadView.as_view()),
    url(r'^upload/success',
        TemplateView.as_view(template_name="success.html"),
        name='upload_success'),
    url(r'^file/(?P<id>[0-9]+)$', views.file),
]
