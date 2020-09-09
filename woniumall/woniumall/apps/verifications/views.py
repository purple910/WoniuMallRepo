import random
from venv import logger

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection
from redis import StrictRedis

from celery_tasks.sms.tasks import send_sms_verification_code
from woniumall.libs.captcha.captcha import captcha
from woniumall.libs.ronglian_sms_sdk.SendMessage import send_message
from woniumall.utils import constants
from woniumall.utils.response_code import RETCODE


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
        response = HttpResponse(image, content_type='image/jpg')
        # response["Access-Control-Allow-Origin"] = '*'
        return response


class SMSCodeView(View):
    """短信验证码"""

    def get(self, reqeust, mobile):
        """
        :param reqeust: 请求对象
        :param mobile: 手机号
        :return: JSON
        """
        # 接收参数
        image_code_client = reqeust.GET.get('image_code')
        uuid = reqeust.GET.get('uuid')

        # 校验参数
        if not all([image_code_client, uuid]):
            return JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少必传参数'})

        # 校验验证码是否再60s里发送
        redis_sms: StrictRedis = get_redis_connection('sms_code')
        send_flag = redis_sms.get('send_flag_%s' % mobile)
        if send_flag:
            return JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '发送短信过于频繁'})

        # 创建连接到图形redis的对象
        redis_conn = get_redis_connection('verify_code')
        # 提取图形验证码
        image_code_server = redis_conn.get(uuid)
        if image_code_server is None:
            # 图形验证码过期或者不存在
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码失效'})

        # 删除图形验证码，避免恶意测试图形验证码
        try:
            redis_conn.delete(uuid)
        except Exception as e:
            logger.error(e)

        # 对比图形验证码
        image_code_server = image_code_server.decode()  # bytes转字符串
        if image_code_client.lower() != image_code_server.lower():  # 转小写后比较
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '输入图形验证码有误'})

        # 创建 sms 的redis
        # redis_conn = get_redis_connection('sms_code')

        # 生成短信验证码：生成6位数验证码
        # sms_code = '{%06d}' % random.randint(0, 999999)
        sms_code = '{:06d}'.format(random.randint(0, 999999))
        # logger.info(sms_code)

        # 保存短信验证码
        # redis_conn.set(mobile, sms_code, ex=constants.SMS_CODE_REDIS_EXPIRES)
        # 写入send_flag
        # redis_conn.set('send_flag_%s' % mobile, 1, ex=constants.SEND_SMS_CODE_INTERVAL)

        # 通过pipeline 有优化redis 保存短信验证码
        pipeline = redis_sms.pipeline()
        pipeline.set(mobile, sms_code, ex=constants.SMS_CODE_REDIS_EXPIRES)
        pipeline.set('send_flag_%s' % mobile, 1, ex=constants.SEND_SMS_CODE_INTERVAL)
        pipeline.execute()

        # 发送短信验证码
        message = send_message(mobile, sms_code)
        if not message:
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '发送短信失败'})

        # 响应结果 异步发送
        # celery worker -A celery_tasks.main -l info -P eventlet
        # send_sms_verification_code.delay(mobile, sms_code)

        response = JsonResponse({'code': RETCODE.OK, 'errmsg': '发送短信成功'})
        # 设置响应头信息, 使其可以跨域
        # response["Access-Control-Allow-Origin"] = '*'
        return response
