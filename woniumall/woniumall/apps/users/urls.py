"""
    @Time    : 2020/8/26 15:27 
    @Author  : fate
    @Site    : 
    @File    : urls.py
    @Software: PyCharm
"""
from django.contrib.auth.decorators import login_required
from django.urls import re_path

from users import views

urlpatterns = [
    re_path(r'register/$', views.RegisterView.as_view()),
    re_path(r'usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/', views.UsernameCountView.as_view()),
    re_path(r'mobiles/(?P<mobile>1[3-9]\d{9})/count/', views.MobileCountView.as_view()),
    re_path(r'^login/$', views.LoginView.as_view(), name='login'),
    re_path(r'^logout/$', views.LogoutView.as_view()),

    # 自己进行 is_authenticated 判断,用户是否登录
    # re_path(r'^info/$', views.UserInfoView.as_view()),
    # 装饰器 login_required, 使其在未登录时跳转到登录界面,后再跳转到info页面
    # re_path(r'^info/$', login_required(views.UserInfoView.as_view())),
    # 继承 LoginRequiredMixin ,使其在未登录时跳转到登录界面,后再跳转到info页面
    re_path(r'^info/$', views.UserInfoView.as_view()),

    re_path(r'^emails/$', views.EmailView.as_view()),
    re_path(r'^password/$', views.ChangePasswordView.as_view()),
]
