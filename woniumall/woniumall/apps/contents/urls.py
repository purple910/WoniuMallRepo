"""
    @Time    : 2020/8/26 15:27 
    @Author  : fate
    @Site    : 
    @File    : urls.py
    @Software: PyCharm
"""
from django.urls import re_path

from contents import views

urlpatterns = [
    re_path(r'^$', views.HomeView.as_view())
]
