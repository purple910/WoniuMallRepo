"""
    @Time    : 2020/9/3 13:46 
    @Author  : fate
    @Site    : 
    @File    : signer.py
    @Software: PyCharm
"""
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature, BadData

from users.models import User
from woniumall.utils import constants


class Signer(object):
    serializer = Serializer(settings.SECRET_KEY, expires_in=constants.OPENID_SIGN_EXPIRES)

    @classmethod
    def sign(cls, obj):
        """
        对python字典先进行json序列化，再对序列化结果进行签名
        :param obj:
        :return: 签名后的字符串
        """
        token = cls.serializer.dumps(obj)
        return token.decode()

    @classmethod
    def unsign(cls, s):
        """
        对传入的字符串验证签名, 验证成功返回字符串中的被签名的数据对应的python字典
        :param s: 要验证的签名字符串
        :return: python字典
        """
        try:
            obj = cls.serializer.loads(s)
        except BadSignature:
            obj = None
        return obj


def check_verify_email_token(token):
    """
    验证token并提取user
    :param token: 用户信息签名后的结果
    :return: user, None
    """
    serializer = Serializer(settings.SECRET_KEY, expires_in=constants.VERIFY_EMAIL_TOKEN_EXPIRES)
    try:
        data = serializer.loads(token)
    except BadData:
        return None
    else:
        user_id = data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
        else:
            return user
