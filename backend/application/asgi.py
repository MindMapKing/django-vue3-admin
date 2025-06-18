"""
ASGI配置文件 - Django应用程序的异步服务器网关接口配置

该文件将ASGI可调用对象作为模块级变量``application``暴露出来。

有关此文件的更多信息，请参阅：
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os  # 导入操作系统接口模块，用于环境变量操作
from channels.auth import AuthMiddlewareStack  # 从channels导入认证中间件栈，用于WebSocket认证
from channels.security.websocket import AllowedHostsOriginValidator  # 导入WebSocket主机来源验证器，用于安全防护
from channels.routing import ProtocolTypeRouter, URLRouter  # 导入协议类型路由器和URL路由器，用于请求路由分发
from django.core.asgi import get_asgi_application  # 导入Django ASGI应用程序获取函数

# 设置Django配置模块的环境变量，指向项目的设置文件
# 设置Django配置模块的环境变量，指向项目的设置文件
# 'application.settings' 指的是 backend/application/ 目录下的 settings.py 文件
# Django会自动将点号(.)转换为目录分隔符，所以 'application.settings' 对应 application/settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings')
# 允许Django在异步环境中运行不安全的代码（主要用于开发环境）
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# 获取Django的ASGI应用程序实例，用于处理HTTP请求
http_application = get_asgi_application()

# 从应用程序路由文件中导入WebSocket URL模式
from application.routing import websocket_urlpatterns

# 创建ASGI应用程序，配置协议类型路由器
application = ProtocolTypeRouter({
    # 配置HTTP协议处理器，使用Django默认的ASGI应用程序
    "http": http_application,
    # 配置WebSocket协议处理器
    'websocket': AllowedHostsOriginValidator(  # 外层：验证请求来源是否在允许的主机列表中
        AuthMiddlewareStack(  # 中层：添加认证中间件栈，处理用户认证
            URLRouter(  # 内层：URL路由器，根据URL模式分发WebSocket连接
                websocket_urlpatterns  # WebSocket路由模式列表，定义在application/routing.py文件中
            )
        )
    ),
})
