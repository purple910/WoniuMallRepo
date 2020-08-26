"""
    @Time    : 2020/8/26 15:27 
    @Author  : fate
    @Site    : 
    @File    : urls.py
    @Software: PyCharm
"""
from django.urls import re_path

from users import views

urlpatterns = [
    re_path(r'register/$', views.RegisterView.as_view())
]
