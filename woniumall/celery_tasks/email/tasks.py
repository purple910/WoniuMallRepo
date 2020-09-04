"""
    @Time    : 2020/9/4 17:28 
    @Author  : fate
    @Site    : 
    @File    : tasks.py
    @Software: PyCharm
"""
from django.conf import settings
from django.core.mail import send_mail

from celery_tasks.main import app


@app.task(name="send_verify_email", bind=True, retry_backoff=3)
def send_verify_email(self, to_email, verify_url):
    """
    发送验证邮件
    :param self:
    :param to_email:
    :param verify_url:
    :return:
    """
    subject = "蜗牛商城邮箱验证"
    html_message = '<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用蜗牛商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s<a></p>' % (to_email, verify_url, verify_url)
    try:
        send_mail(subject, "", settings.EMAIL_FROM, [to_email], html_message=html_message)
    except Exception as e:
        raise self.retry(exc=e, max_retries=3)
