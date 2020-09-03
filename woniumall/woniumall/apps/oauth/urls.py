"""
    @Time    : 2020/9/3 13:24 
    @Author  : fate
    @Site    : 
    @File    : urls.py
    @Software: PyCharm
"""
from django.urls import re_path

from oauth import views

urlpatterns = [
    # 生成扫码登录页面链接
    re_path(r'^qq/login/$', views.QQAuthURLView.as_view()),
    # 接收Authorization Code
    re_path(r'^oauth_callback/$', views.QQAuthUserView.as_view()),

]
