import re
from venv import logger

from QQLoginTool.QQtool import OAuthQQ
from django.contrib.auth import login
# from django.core.signing import Signer
from django.db import DatabaseError
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseServerError, HttpRequest
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection

from oauth.models import OAuthQQUser
from oauth.utils import Signer
from users.models import User
from woniumall.settings import dev
from woniumall.utils import constants
from woniumall.utils.response_code import RETCODE


class QQAuthURLView(View):
    """提供QQ登录页面网址
    https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=xxx&redirect_uri=xxx&state=xxx
    """

    def get(self, request):
        # next表示从哪个页面进入到的登录页面，将来登录成功后，就自动回到那个页面
        next = request.GET.get('next')

        # 获取QQ登录页面网址
        oauth = OAuthQQ(client_id=dev.QQ_CLIENT_ID, client_secret=dev.QQ_CLIENT_SECRET,
                        redirect_uri=dev.QQ_REDIRECT_URI, state=next)
        login_url = oauth.get_qq_url()

        return JsonResponse({'code': RETCODE.OK,
                             'errmsg': 'OK',
                             'login_url': login_url})


class QQAuthUserView(View):
    """用户扫码登录的回调处理"""

    def get(self, request):
        """Oauth2.0认证"""
        # 接收Authorization Code
        code = request.GET.get('code')
        if not code:
            return HttpResponseForbidden('缺少code')

        # 创建工具对象
        oauth = OAuthQQ(client_id=dev.QQ_CLIENT_ID, client_secret=dev.QQ_CLIENT_SECRET,
                        redirect_uri=dev.QQ_REDIRECT_URI)

        try:
            # 使用code向QQ服务器请求access_token
            access_token = oauth.get_access_token(code)

            # 使用access_token向QQ服务器请求openid
            openid = oauth.get_open_id(access_token)
        except Exception as e:
            logger.error(e)
            return HttpResponseServerError('OAuth2.0认证失败')

        try:
            oauth_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 如果openid没绑定蜗牛商城用户
            access_token = Signer.sign(openid)
            context = {'token': access_token}
            return render(request, 'oauth_callback.html', context)
        else:
            # 如果openid已绑定蜗牛商城用户
            # 实现状态保持
            qq_user = oauth_user.user
            # 没有认证登录用户,则要自定义backend
            login(request, qq_user, backend='django.contrib.auth.backends.ModelBackend')

            # 响应结果
            # next = request.GET.get('state', '/')
            # response = redirect(next)

            # 重定向到主页
            response = redirect(reverse('contents:index'))

            # 登录时用户名写入到cookie，有效期15天
            response.set_cookie('username', qq_user.username, max_age=3600 * 24 * 15)

            return response

    def post(self, request: HttpRequest):
        """绑定蜗牛商城用户和openid"""
        # http://www.meiduo.site:8000/oauth_callback/?code=DC72C8A28F03EC1B577360FB6E8FBA95&state=%2F
        # 提取数据
        access_token = request.POST.get('access_token')
        mobile = request.POST.get("mobile")
        password = request.POST.get("password")
        sms_code = request.POST.get("sms_code")
        state = request.GET.get("state")

        # 校验数据
        # 检查参数是否齐全
        if not all([mobile, password, sms_code, access_token]):
            return HttpResponseForbidden("缺少必须的数据")

        # 判断手机号格式是否正确
        if not re.match(r"^1[345789]\d{9}$", mobile):
            return HttpResponseForbidden("手机号码格式错误")

        # 判断密码格式是否正确
        if not re.match(r"^[0-9A-Za-z]{8,20}$", password):
            return HttpResponseForbidden("密码格式错误")

        # 判断短信验证码是否一致
        conn = get_redis_connection("sms_code")
        sms_code_server = conn.get(mobile)
        if sms_code_server is None:
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '短信验证码已失效'})
        if sms_code != sms_code_server.decode():
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '短信验证码错误'})

        # 判断openid是否有效
        open_id = Signer.unsign(access_token)
        if open_id is None:
            return render(request, 'oauth_callback.html', {'openid_errmsg': '无效的openid'})
        # else:
        # open_id = open_id["open_id"]

        # 处理逻辑
        try:
            # 查询手机号用户是否存在
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 用户不存在, 创建用户
            user = User.objects.create_user(username=mobile, mobile=mobile, password=password)
        else:
            # 用户存在,检查用户密码是否正确
            if not user.check_password(password):
                return render(request, 'oauth_callback.html', {'account_errmsg': '用户名或密码错误'})
        # 绑定用户
        try:
            OAuthQQUser.objects.create(user=user, openid=open_id)
        except DatabaseError:
            return render(request, 'oauth_callback.html', {'qq_login_errmsg': 'QQ登录失败'})

        # 登陆状态保持
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        response = redirect(state)
        # 登陆时把用户名写入 cookie
        response.set_cookie("username", user.username, expires=constants.USERNAME_COOKIE_EXPIRES)

        # 响应
        return response
