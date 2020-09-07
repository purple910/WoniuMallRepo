"""
    @Time    : 2020/8/28 15:50 
    @Author  : fate
    @Site    : 
    @File    : constants.py
    @Software: PyCharm
"""
# 图形验证码的有效期 60s
IMAGE_CODE_REDIS_EXPIRES = 60
# 短信验证码的有效期 300s
SMS_CODE_REDIS_EXPIRES = 60 * 5
# 判断短信发送后再redis的存活,避免频繁发送
SEND_SMS_CODE_INTERVAL = 60
# 地址上限：最多20个
USER_ADDRESS_COUNTS_LIMIT = 20
# 密钥的有效期
OPENID_SIGN_EXPIRES = 300
# qq绑定用户的有效期
USERNAME_COOKIE_EXPIRES = 60 * 60 * 24 * 14
# 验证邮箱的有效期
VERIFY_EMAIL_TOKEN_EXPIRES = 60 * 60
# 收货地址的缓存
AREA_CACHE_EXPIRES = 3600
