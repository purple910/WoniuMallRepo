"""
    @Time    : 2020/8/28 15:22 
    @Author  : fate
    @Site    : 
    @File    : urls.py
    @Software: PyCharm
"""
from django.urls import re_path

from verifications import views

urlpatterns = [
    re_path(r'^image_codes/(?P<uuid>[\w-]+)/$', views.ImageCodeView.as_view())
]
