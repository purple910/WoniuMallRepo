"""
    @Time    : 2020/9/2 11:06 
    @Author  : fate
    @Site    : 手机号登录
    @File    : auth_backend.py
    @Software: PyCharm
"""
import re

from django.contrib.auth.backends import BaseBackend, UserModel

from users.models import User


class MobilePasswordBackend(BaseBackend):
    def authenticate(self, request, **kwargs):
        mobile = kwargs.get('username')
        password = kwargs.get('password')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return

        try:
            # 通过手机号查询数据库
            user = UserModel.objects.get(mobile=mobile)
        except UserModel.DoesNotExist:
            return

        if user.check_password(password):
            return user
