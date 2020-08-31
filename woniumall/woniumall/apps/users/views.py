import re

from django.contrib.auth import authenticate, login, logout
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

        # 响应登录结果
        response = redirect('/')

        # 登录时用户名写入到cookie，有效期15天
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)

        return response


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


class LoginView(View):
    """用户名登录"""

    def get(self, request):
        """
        提供登录界面
        :param request: 请求对象
        :return: 登录界面
        """
        return render(request, 'login.html')

    def post(self, request):
        """
        实现登录逻辑
        :param request: 请求对象
        :return: 登录结果
        """
        # 接受参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        # 校验参数
        # 判断参数是否齐全
        if not all([username, password]):
            return HttpResponseForbidden('缺少必传参数')

        # 判断用户名是否是5-20个字符
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return HttpResponseForbidden('请输入正确的用户名或手机号')

        # 判断密码是否是8-20个数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseForbidden('密码最少8位，最长20位')

        # 认证登录用户
        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})

        # 实现状态保持
        login(request, user)
        # 设置状态保持的周期
        if remembered != 'on':
            # 没有记住用户：浏览器会话结束就过期
            request.session.set_expiry(0)
        else:
            # 记住用户：None表示两周后过期
            request.session.set_expiry(None)

        # 响应登录结果
        response = redirect('/')

        # 登录时用户名写入到cookie，有效期15天
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)

        return response


class LogoutView(View):
    """退出登录"""

    def get(self, request):
        """实现退出登录逻辑"""
        # 清理session
        logout(request)
        # 退出登录，重定向到登录页
        response = redirect('/')
        # 退出登录时清除cookie中的username
        response.delete_cookie('username')

        return response


class UserInfoView(View):
    """用户中心"""

    def get(self, request):
        """提供个人信息界面"""
        if request.user.is_authenticated:
            context = {
                'username': request.user.username,
                'mobile': request.user.mobile,
                'email': request.user.email,
                'email_active': request.user.email_active
            }
            return render(request, 'user_center_info.html', context=context)
        else:
            return redirect('/login/')



