"""
WSGI 配置文件
=============

WSGI (Web Server Gateway Interface) 是Python Web应用程序与Web服务器之间的标准接口。
该文件是Django项目的WSGI配置入口，主要用于：

1. **生产环境部署**：与Apache、Nginx+uWSGI、Gunicorn等Web服务器集成
2. **应用程序入口**：作为Django应用的WSGI callable入口点
3. **环境配置**：设置Django运行时的环境变量和配置

部署场景：
- Apache + mod_wsgi：直接使用此文件作为WSGIScriptAlias目标
- Nginx + uWSGI：uWSGI服务器通过此文件启动Django应用
- Gunicorn：通过 gunicorn application.wsgi:application 命令启动
- Docker部署：容器化部署时的应用入口

相关文档：
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# 设置Django配置模块的环境变量
# 这告诉Django使用哪个settings模块作为项目配置
# 'application.settings' 对应 application/settings.py 文件
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings')

# 允许在非异步环境中运行异步代码（用于兼容性）
# 这个设置解决了Django在某些WSGI服务器环境中的异步兼容性问题
# 注意：在生产环境中需要谨慎使用，可能影响性能
# 主要用于解决ORM在WSGI环境中的异步查询问题
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# 创建WSGI应用程序对象
# 这是WSGI规范要求的callable对象，Web服务器会调用它来处理HTTP请求
# get_wsgi_application() 函数：
# 1. 加载Django设置
# 2. 配置URL路由
# 3. 初始化中间件
# 4. 返回符合WSGI规范的application callable
application = get_wsgi_application()

# WSGI应用程序对象说明：
# - 'application' 是WSGI规范定义的标准名称
# - Web服务器通过调用 application(environ, start_response) 来处理请求
# - environ: 包含HTTP请求信息的字典
# - start_response: 用于发送HTTP响应头的回调函数
#
# 使用示例：
# 1. Gunicorn: gunicorn application.wsgi:application
# 2. uWSGI: uwsgi --module=application.wsgi:application
# 3. Apache mod_wsgi: WSGIScriptAlias / /path/to/application/wsgi.py
