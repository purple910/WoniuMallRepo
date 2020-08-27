import re

from django.contrib.auth import authenticate, login
from django.db import DatabaseError
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View

from users.models import User


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        """

        :param request:
        :return:
        """
        # 1.获取数据
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        pic_code = request.POST.get('pic_code')
        sms_code = request.POST.get('sms_code')
        allow = request.POST.get('allow')

        # 2.校验数据
        # 判断参数是否齐全
        if not all([username, password, password2, mobile, sms_code, allow]):
            return HttpResponseForbidden("缺少必须的参数")

        # 判断用户名 5-20 字符
        if re.match(r'^[0-9a-zA-Z_-]{5,20}$', username) is None:
            return HttpResponseForbidden("用户名必须是5-20的字符")

        # 判断密码是否是8-20个字符
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseForbidden('请输入8-20位的密码')

        # 判断两次密码是否一致

        if password != password2:
            return HttpResponseForbidden('两次输入的密码不一致')

        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('请输入正确的手机号码')

        # 判断是否勾选用户协议
        if allow != 'on':
            return HttpResponseForbidden('请勾选用户协议')

        # 用户名是否存在
        users: QuerySet = User.objects.filter(username=username)
        if users.count() > 0:
            return HttpResponseForbidden("用户名重复")

        # 手机号是否存在
        if User.objects.filter(mobile=mobile).count() > 0:
            return HttpResponseForbidden("手机号重复")

        # TODO 校验短信验证码

        # 保存注册数据
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render(request, "register.html", {'register_errmsg': '注册失败'})

        # 用户登录,保持session 用户注册不用再登录
        # user = authenticate(username=username, password=password)
        login(request, user)

        # 转发
        return redirect('/')


class UsernameCountView(View):
    """判断用户名是否重复注册"""

    def get(self, request, username):
        """

        :param request:请求对象
        :param username:用户名
        :return:JSON
        """
        count = User.objects.filter(username=username).count()
        # print('1111111')
        return JsonResponse({'code': 'OK', 'errmsg': 'OK', 'count': count})


class MobileCountView(View):
    """判断手机号是否重复注册"""

    def get(self, request, mobile):
        """
        :param request: 请求对象
        :param mobile: 手机号
        :return: JSON
        """
        count = User.objects.filter(mobile=mobile).count()
        return JsonResponse({'code': 'OK', 'errmsg': 'OK', 'count': count})



