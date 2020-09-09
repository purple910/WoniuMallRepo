import json
import re
from venv import logger

from django import http
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import DatabaseError
from django.db.models import QuerySet
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, HttpResponseBadRequest, \
    HttpResponseServerError, HttpRequest
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection

from celery_tasks.email.tasks import send_verify_email
from users.models import User, Area, Address
from woniumall.utils import constants
from woniumall.utils.mixin import LoginRequireJsonMixin
from woniumall.utils.response_code import RETCODE
from woniumall.utils.signer import Signer, check_verify_email_token, generate_verify_email_url


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        response = render(request, 'register.html')
        # response["Access-Control-Allow-Origin"] = '*'
        return response

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

        # 校验短信验证码
        redis_conn = get_redis_connection('sms_code')
        sms_code_server = redis_conn.get(mobile)
        if sms_code_server is None:
            return render(request, 'register.html', {'sms_code_errmsg': '无效的短信验证码'})
        if sms_code != sms_code_server.decode():
            return render(request, 'register.html', {'sms_code_errmsg': '输入短信验证码有误'})

        # 保存注册数据
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render(request, "register.html", {'register_errmsg': '注册失败'})

        # 用户登录,保持session 用户注册不用再登录
        # user = authenticate(username=username, password=password)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # 响应登录结果
        response = redirect('/')

        # 登录时用户名写入到cookie，有效期15天
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
        # response["Access-Control-Allow-Origin"] = '*'
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
        response = JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})
        # response["Access-Control-Allow-Origin"] = '*'
        return response


class MobileCountView(View):
    """判断手机号是否重复注册"""

    def get(self, request, mobile):
        """
        :param request: 请求对象
        :param mobile: 手机号
        :return: JSON
        """
        count = User.objects.filter(mobile=mobile).count()
        response = JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})
        # response["Access-Control-Allow-Origin"] = '*'
        return response


class LoginView(View):
    """用户名登录"""

    def get(self, request):
        """
        提供登录界面
        :param request: 请求对象
        :return: 登录界面
        """
        response = render(request, 'login.html')
        # response["Access-Control-Allow-Origin"] = '*'
        return response

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
        # response = redirect('/')
        # 判断是否是去首页
        # http://127.0.0.1:8000/login/?next=/info/ 实际上要在登陆后跳转到info页面
        next = request.GET.get('next')
        if next:
            response = redirect(next)
        else:
            response = redirect(reverse('contents:index'))

        if remembered != 'on':
            # 设置cookie 为关闭浏览器则有效期结束
            response.set_cookie('username', user.username)
        else:
            # 登录时用户名写入到cookie，有效期14天
            response.set_cookie('username', user.username, max_age=3600 * 24 * 14)
        # response["Access-Control-Allow-Origin"] = '*'
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
        # response["Access-Control-Allow-Origin"] = '*'
        return response


class UserInfoView(LoginRequiredMixin, View):
    """用户中心"""

    # def get(self, request):
    #     """提供个人信息界面"""
    #     if request.user.is_authenticated:
    #         context = {
    #             'username': request.user.username,
    #             'mobile': request.user.mobile,
    #             'email': request.user.email,
    #             'email_active': request.user.email_active
    #         }
    #         return render(request, 'user_center_info.html', context=context)
    #     else:
    #         # return redirect('/login/')
    #         return redirect(reverse('users:login'))

    def get(self, request):
        """提供个人信息界面"""
        context = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active
        }
        response = render(request, 'user_center_info.html', context=context)
        # response["Access-Control-Allow-Origin"] = '*'
        return response


class EmailView(LoginRequireJsonMixin, View):
    """添加邮箱"""

    def put(self, request):
        """实现添加邮箱逻辑"""
        # 判断用户是否登录并返回JSON
        # if not request.user.is_authenticated:
        #     return JsonResponse({'code': RETCODE.SESSIONERR, 'errmsg': '用户未登录'})

        # 接收参数
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')

        # 校验参数
        if not email:
            return HttpResponseForbidden('缺少email参数')
        # if not re.match(r'^([a-zA-Z0-9_-])+@([a-zA-Z0-9_-])+(.[a-zA-Z0-9_-])+', email):
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return HttpResponseForbidden('参数email有误')

        # 赋值email字段
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '添加邮箱失败'})

        # 发送邮箱验证邮件
        verify_url = settings.EMAIL_VERIFY_URL + '?token=' + Signer.sign({"user_id": request.user.id})
        subject = "蜗牛商城邮箱验证"
        message = ""
        from_email = settings.EMAIL_FROM
        recipient_list = [email]
        html_message = '<p>尊敬的用户您好！</p>' \
                       '<p>感谢您使用蜗牛商城。</p>' \
                       '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                       '<p><a href="%s">%s<a></p>' % (email, verify_url, verify_url)
        send_mail(subject=subject, message=message, from_email=from_email, recipient_list=recipient_list,
                  html_message=html_message)

        # 异步发送验证邮件
        # verify_url = generate_verify_email_url(request.user.id)
        # send_verify_email.delay(email, verify_url)

        # 响应添加邮箱结果
        response = JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱成功'})
        # response["Access-Control-Allow-Origin"] = '*'
        return response


class VerifyEmailView(View):
    """验证邮箱"""

    def get(self, request):
        """实现邮箱验证逻辑"""
        # 接收参数
        token = request.GET.get('token')

        # 校验参数：判断token是否为空和过期，提取user
        if not token:
            return HttpResponseBadRequest('缺少token')

        user = check_verify_email_token(token)
        if not user:
            return HttpResponseForbidden('无效的token')

        # 修改email_active的值为True
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            logger.error(e)
            return HttpResponseServerError('激活邮件失败')

        # 返回邮箱验证结果
        response = redirect(reverse('users:info'))
        # response["Access-Control-Allow-Origin"] = '*'
        return response


class ChangePasswordView(LoginRequiredMixin, View):
    """修改密码"""

    def get(self, request):
        """展示修改密码界面"""
        response = render(request, 'user_center_pass.html')
        # response["Access-Control-Allow-Origin"] = '*'
        return response

    def post(self, request):
        """实现修改密码逻辑"""
        # 接收参数
        old_password = request.POST.get('old_pwd')
        new_password = request.POST.get('new_pwd')
        new_password2 = request.POST.get('new_cpwd')

        # 校验参数
        if not all([old_password, new_password, new_password2]):
            return HttpResponseForbidden('缺少必传参数')
        try:
            request.user.check_password(old_password)
        except Exception as e:
            logger.error(e)
            return render(request, 'user_center_pass.html', {'origin_pwd_errmsg': '原始密码错误'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return HttpResponseForbidden('密码最少8位，最长20位')
        if new_password != new_password2:
            return HttpResponseForbidden('两次输入的密码不一致')

        # 修改密码
        try:
            request.user.set_password(new_password)
            request.user.save()
        except Exception as e:
            logger.error(e)
            return render(request, 'user_center_pass.html', {'change_pwd_errmsg': '修改密码失败'})

        # 清理状态保持信息
        logout(request)
        response = redirect('/login/')
        response.delete_cookie('username')
        # response["Access-Control-Allow-Origin"] = '*'

        # # 响应密码修改结果：重定向到登录界面
        return response


class AddressView(LoginRequiredMixin, View):
    """用户收货地址"""

    def get(self, request):
        """提供收货地址界面"""
        # 获取用户地址列表
        login_user = request.user
        addresses = Address.objects.filter(user=login_user, is_deleted=False)

        address_dict_list = []
        for address in addresses:
            address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "province_id": address.province_id,
                "city": address.city.name,
                "city_id": address.city_id,
                "district": address.district.name,
                "district_id": address.district_id,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            }
            address_dict_list.append(address_dict)

        context = {
            'default_address_id': login_user.default_address_id,
            'addresses': address_dict_list,
        }

        response = render(request, 'user_center_site.html', context)
        # response["Access-Control-Allow-Origin"] = '*'
        return response


class AreasView(View):
    """省市区数据"""

    def get(self, request):
        """提供省市区数据"""
        area_id = request.GET.get('area_id')

        if not area_id:
            # 缓存
            province_list = cache.get("province_list")

            # 提供省份数据
            if province_list is None:
                try:
                    # 查询省份数据
                    province_model_list = Area.objects.filter(parent__isnull=True)

                    # 序列化省级数据
                    province_list = []
                    for province_model in province_model_list:
                        province_list.append({'id': province_model.id, 'name': province_model.name})
                except Exception as e:
                    logger.error(e)
                    return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '省份数据错误'})

                # 添加缓存
                cache.set("province_list", province_list, constants.AREA_CACHE_EXPIRES)

            # 响应省份数据
            response = JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})
        else:
            # 读取市或区缓存数据
            sub_data = cache.get('sub_area_' + area_id)

            if not sub_data:
                # 提供市或区数据
                try:
                    parent_model = Area.objects.get(id=area_id)  # 查询市或区的父级
                    sub_model_list = parent_model.subs.all()

                    # 序列化市或区数据
                    sub_list = []
                    for sub_model in sub_model_list:
                        sub_list.append({'id': sub_model.id, 'name': sub_model.name})

                    sub_data = {
                        'id': parent_model.id,  # 父级pk
                        'name': parent_model.name,  # 父级name
                        'subs': sub_list  # 父级的子集
                    }
                except Exception as e:
                    logger.error(e)
                    return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '城市或区数据错误'})
                # 储存市或区缓存数据
                cache.set('sub_area_' + area_id, sub_data, constants.AREA_CACHE_EXPIRES)

            # 响应市或区数据
            response = JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sub_data': sub_data})

        # response["Access-Control-Allow-Origin"] = '*'
        return response


class CreateAddressView(LoginRequireJsonMixin, View):
    """新增地址"""

    def post(self, request):
        """实现新增地址逻辑"""
        # 判断是否超过地址上限：最多20个
        # Address.objects.filter(user=request.user).count()
        count = request.user.addresses.count()
        if count >= constants.USER_ADDRESS_COUNTS_LIMIT:
            return JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '超过地址数量上限'})

        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return HttpResponseForbidden('参数email有误')

        # 保存地址信息
        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )

            # 设置默认地址
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '新增地址失败'})

        # 新增地址成功，将新增的地址响应给前端实现局部刷新
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应保存结果
        response = JsonResponse({'code': RETCODE.OK, 'errmsg': '新增地址成功', 'address': address_dict})
        # response["Access-Control-Allow-Origin"] = '*'
        return response


class DefaultAddressView(LoginRequireJsonMixin, View):
    """设置默认地址"""

    def put(self, request, address_id):
        """设置默认地址"""
        try:
            # 接收参数,查询地址
            address = Address.objects.get(id=address_id)

            # 设置地址为默认地址
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置默认地址失败'})

        # 响应设置默认地址结果
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})
        # response["Access-Control-Allow-Origin"] = '*'
        return response


class UpdateTitleAddressView(LoginRequireJsonMixin, View):
    """设置地址标题"""

    def put(self, request, address_id):
        """设置地址标题"""
        # 接收参数：地址标题
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        try:
            # 查询地址
            address = Address.objects.get(id=address_id)

            # 设置新的地址标题
            address.title = title
            address.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置地址标题失败'})

        # 4.响应删除地址结果
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '设置地址标题成功'})
        # response["Access-Control-Allow-Origin"] = '*'
        return response


class UpdateDestroyAddressView(LoginRequireJsonMixin, View):
    """修改和删除地址"""

    def put(self, request, address_id):
        """修改地址"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        # 判断地址是否存在,并更新地址信息
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '更新地址失败'})

        # 构造响应数据
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "province_id": address.province_id,
            "city": address.city.name,
            "city_id": address.city_id,
            "district": address.district.name,
            "district_id": address.district_id,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应更新地址结果
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '更新地址成功', 'address': address_dict})
        # response["Access-Control-Allow-Origin"] = '*'
        return response

    def delete(self, request, address_id):
        """删除地址"""
        try:
            # 查询要删除的地址
            address = Address.objects.get(id=address_id)

            # 将地址逻辑删除设置为True
            address.is_deleted = True
            address.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '删除地址失败'})

        # 响应删除地址结果
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})
        # response["Access-Control-Allow-Origin"] = '*'
        return response
