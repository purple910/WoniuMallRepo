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
    'environment': 'woniumall.utils.jinja2_env.jinja2_environment'
```

# 配置redirect
## 全局的urls
```
re_path(r'^', include(('areas.urls', 'areas')))
```
## 局部的urls
```
re_path(r'^addresses/$', views.AddressView.as_view(), name='address'),
re_path(r'^aaa',views.Aa.as_view())
```
## view
```
class AddressView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'user_center_site.html')

class Aa(View):
    def get(self, request):
        return redirect(reverse('areas:address'))
```

# authenticate 用户名或手机号登录
## settings/dev.py
```
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend', 'users.auth_backend.MobilePasswordBackend']
```
## auth_backend.py
```
class MobilePasswordBackend(BaseBackend):
    def authenticate(self, request, **kwargs):
        mobile = kwargs.get('username')
        password = kwargs.get('password')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return

        try:
            # 通过手机号查询数据库
            user = UserModel.objects.get(mobile=mobile)
        except UserModel.DoesNotExist:
            return

        if user.check_password(password):
            return user
```
## 运行流程
```
1 加载 dev.py
2 触发 users.views.LoginView
    user = authenticate(username=username, password=password)
3 循环 _get_backends(return_tuples=True)
4 先到 django.contrib.auth.backends.ModelBackend里, 用username到数据库里找
5 没有找到, 返回循环 _get_backends(return_tuples=True)
6 再到 users.auth_backend.MobilePasswordBackend里, 用mobile在数据里找
```
## 如果没有认证用户(authenticate),则实现状态保持(login)时要指定认证后端(backend)

## 跨域问题(二选一)
```
1. 再返回时设置response的请求头
    response["Access-Control-Allow-Origin"] = '*'
2. 可以再配置文件配置跨域
    a) pip install django-core-header
    b) INSTALLED_APPS 里面添加 corsheaders 
    c) MIDDLEWARE 里面添加 corsheaders.middleware.CorsMiddleware,django.middleware.common.CommonMiddleware
    d) CORS_ORIGIN_ALLOW_ALL = True, CORS_ALLOW_CREDENTIALS = True
    e) 配置允许访问的连接 CORS_ORIGIN_WHITELIST = ('http://127.0.0.1:8080', 'http://localhost:8080', 'http://www.meiduo.site:8080',)
    f) 配置访问方式 CORS_ALLOW_METHODS = ('DELETE','GET','OPTIONS','PATCH','POST','PUT','VIEW',)
    g) 配置允许访问的请求头
    CORS_ALLOW_HEADERS = (
        'XMLHttpRequest',
        'X_FILENAME',
        'accept-encoding',
        'authorization',
        'content-type',
        'dnt',
        'origin',
        'user-agent',
        'x-csrftoken',
        'x-requested-with',
        'Pragma',
    )
```

## cookie无妨传递
```
// 允许携带cookie
axios.withCredentials = true;
axios.defaults.withCredentials = true
// 若127.0.0.1:8000可以而www.meiduo.site不可以
则是因为前端的host被设置为 127.0.0.1:8000
```
