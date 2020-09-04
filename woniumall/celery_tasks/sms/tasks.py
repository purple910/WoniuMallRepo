"""
    @Time    : 2020/9/1 14:08 
    @Author  : fate
    @Site    : 
    @File    : tasks.py
    @Software: PyCharm
"""
# bind：保证task对象会作为第一个参数自动传入
# name：异步任务别名
# retry_backoff：异常自动重试的时间间隔 第n次(retry_backoff×2^(n-1))s
# max_retries：异常自动重试次数的上限
from celery_tasks.main import app
from woniumall.libs.ronglian_sms_sdk.SendMessage import send_message


@app.task(name="send_sms_verification_code", bind=True, retry_backoff=3)
def send_sms_verification_code(self, mobile, sms_code):
    """

    :param self:
    :param mobile:
    :param sms_code:
    :return:
    """
    try:
        message = send_message(mobile, sms_code)
    except Exception as e:
        raise self.retry(exc=e, max_retries=3)

    if not message:
        # 有异常自动重试三次
        raise self.retry(exc=Exception('发送短信失败'), max_retries=3)

    return message
