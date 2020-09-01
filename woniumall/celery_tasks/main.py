"""
    @Time    : 2020/9/1 14:05 
    @Author  : fate
    @Site    : 
    @File    : main.py
    @Software: PyCharm
"""
# celery启动文件
import os
import sys

from celery import Celery

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)


# 创建celery实例
app = Celery('woniumall')
# 加载celery配置
app.config_from_object('celery_tasks.config')
# 自动注册celery任务
app.autodiscover_tasks(['celery_tasks.sms'])
