# 配置 jinja2
```
TEMPLATES: 
    'BACKEND': 'django.template.backends.jinja2.Jinja2'

# 'django.contrib.admin',
# path('admin/', admin.site.urls),
```
## 创建Jinja2环境配置函数
```
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
```
```
TEMPLATES 
    'environment': 'meiduo_mall.utils.jinja2_env.jinja2_environment'
```

