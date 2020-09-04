"""
    @Time    : 2020/9/4 15:47 
    @Author  : fate
    @Site    : 
    @File    : mixin.py
    @Software: PyCharm
"""
from django.contrib.auth.mixins import AccessMixin
from django.http import JsonResponse

from woniumall.utils.response_code import RETCODE


class LoginRequireJsonMixin(AccessMixin):
    """自定义的登录验证"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        return JsonResponse({'code': RETCODE.SESSIONERR, 'errmsg': '用户未登录'})
