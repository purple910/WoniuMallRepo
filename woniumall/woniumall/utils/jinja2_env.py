"""
    @Time    : 2020/8/25 10:36 
    @Author  : fate
    @Site    : 
    @File    : jinja2_env.py
    @Software: PyCharm
"""
from jinja2 import Environment
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse


def jinja2_environment(**options):
    """创建 jinja2 环境对象"""
    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': reverse,
    })
    return env
