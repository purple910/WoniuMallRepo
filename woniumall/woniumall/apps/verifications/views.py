from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection
from redis import StrictRedis

from woniumall.libs.captcha.captcha import captcha
from woniumall.utils import constants


class ImageCodeView(View):
    """图形验证码"""

    def get(self, request: HttpRequest, uuid):
        """
        :param request: 请求对象
        :param uuid: 唯一标识图形验证码所属于的用户
        :return: image/jpg
        """
        # 生成图片验证码
        _, text, image = captcha.generate_captcha()

        # 保存图片验证码
        # 连接redis
        redis_conn: StrictRedis = get_redis_connection('verify_code')
        redis_conn.set(uuid, text, ex=constants.IMAGE_CODE_REDIS_EXPIRES)
        # redis_conn.setex('img_%s' % uuid, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        # 响应图片验证码
        return HttpResponse(image, content_type='image/jpg')
