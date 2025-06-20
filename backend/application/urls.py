"""
Django 项目主路由配置文件

这是 Django-Vue3-Admin 项目的核心 URL 路由配置文件，负责将 HTTP 请求的 URL 映射到对应的视图函数或类。
该文件定义了整个项目的 URL 路由规则，包括 API 接口、认证、文档、静态文件等路由配置。

主要功能模块：
1. API 接口路由 - 系统核心业务接口
2. 认证路由 - 登录、登出、令牌刷新等
3. API 文档路由 - Swagger 和 ReDoc 文档
4. 静态文件路由 - 媒体文件和静态资源
5. 前端页面路由 - Web 应用页面访问
6. 插件路由 - 动态加载的插件路由
7. 开发调试路由 - 开发环境专用接口

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# ================================================= #
# ******************** 核心依赖导入 ***************** #
# ================================================= #

# Django 核心 URL 和静态文件处理
from django.conf.urls.static import static  # 静态文件 URL 配置
from django.urls import path, include, re_path  # URL 路径配置函数
from django.http import Http404, HttpResponse  # HTTP 响应类
from django.shortcuts import render  # 模板渲染函数

# API 文档生成相关
from drf_yasg import openapi  # OpenAPI 规范定义
from drf_yasg.views import get_schema_view  # API 文档视图生成器
from rest_framework import permissions  # REST Framework 权限类

# JWT 认证相关
from rest_framework_simplejwt.views import (
    TokenRefreshView,  # JWT 令牌刷新视图
)

# 系统内部模块导入
from application import dispatch  # 系统调度模块 - 用于初始化系统配置
from application import settings  # 项目配置文件

# 系统核心视图导入
from dvadmin.system.views.dictionary import InitDictionaryViewSet  # 数据字典初始化视图
from dvladmin.system.views.login import (  # 登录认证相关视图
    LoginView,      # 登录视图
    CaptchaView,    # 验证码视图
    ApiLogin,       # API 登录视图
    LogoutView,     # 登出视图
    LoginTokenView  # 登录令牌视图（开发用）
)
from dvadmin.system.views.system_config import InitSettingsViewSet  # 系统设置初始化视图

# 自定义 Swagger 配置
from dvadmin.utils.swagger import CustomOpenAPISchemaGenerator  # 自定义 OpenAPI 生成器

# 文件类型检测和操作系统相关
import mimetypes  # MIME 类型检测
import os  # 操作系统接口

# ================================================= #
# ******************** 系统初始化 ******************* #
# ================================================= #

# 系统启动时自动执行的初始化操作
# 这些函数会在 Django 应用启动时被调用，确保系统配置和数据字典的正确初始化
dispatch.init_system_config()  # 初始化系统配置参数
dispatch.init_dictionary()     # 初始化数据字典

# ================================================= #
# ******************** API 文档配置 ***************** #
# ================================================= #

# Swagger/OpenAPI 文档配置
# 创建 API 文档的 schema 视图，用于生成和展示 API 文档
schema_view = get_schema_view(
    openapi.Info(
        title="Django-Vue3-Admin API",  # API 文档标题
        default_version="v1",           # API 版本
        description="Django-Vue3-Admin 管理系统 API 文档",  # API 描述
        terms_of_service="https://www.google.com/policies/terms/",  # 服务条款
        contact=openapi.Contact(email="contact@dvadmin.local"),     # 联系方式
        license=openapi.License(name="MIT License"),                # 许可证
    ),
    public=True,  # 是否公开访问
    permission_classes=(permissions.IsAuthenticated,),  # 访问权限：需要认证
    generator_class=CustomOpenAPISchemaGenerator,       # 使用自定义的 Schema 生成器
)

# ================================================= #
# ******************** 前端页面处理函数 *************** #
# ================================================= #

def web_view(request):
    """
    前端 Web 应用主页视图函数
    
    用于渲染前端 Vue3 应用的主页面，通常是单页应用(SPA)的入口点。
    在前后端分离的架构中，这个视图负责提供前端应用的 HTML 容器。
    
    Args:
        request: HTTP 请求对象
        
    Returns:
        HttpResponse: 渲染后的 HTML 响应
    """
    return render(request, 'web/index.html')


def serve_web_files(request, filename):
    """
    前端静态文件服务函数
    
    用于处理前端应用的静态资源文件请求，如 JavaScript、CSS、图片等。
    这个函数主要用于开发环境，生产环境建议使用 Nginx 等 Web 服务器处理静态文件。
    
    Args:
        request: HTTP 请求对象
        filename: 请求的文件名（包含路径）
        
    Returns:
        HttpResponse: 文件内容响应
        
    Raises:
        Http404: 当请求的文件不存在时抛出 404 错误
    """
    # 构建完整的文件路径
    # 将文件名与模板目录和 web 子目录组合成完整路径
    filepath = os.path.join(settings.BASE_DIR, 'templates', 'web', filename)

    # 安全性检查：验证文件是否存在
    # 防止访问不存在的文件，避免服务器错误
    if not os.path.exists(filepath):
        raise Http404("File does not exist")

    # 根据文件扩展名自动检测 MIME 类型
    # 确保浏览器能够正确处理不同类型的文件（如 CSS、JS、图片等）
    mime_type, _ = mimetypes.guess_type(filepath)

    # 以二进制模式打开文件并读取内容
    # 使用二进制模式确保能够正确处理各种文件类型
    with open(filepath, 'rb') as f:
        # 创建 HTTP 响应对象，设置正确的 Content-Type
        response = HttpResponse(f.read(), content_type=mime_type)
        return response

# ================================================= #
# ******************** URL 路由配置 ***************** #
# ================================================= #

# 主 URL 模式配置列表
# 定义了整个项目的 URL 路由规则，按功能模块组织
urlpatterns = (
        [
            # ============= API 文档路由 =============
            # Swagger JSON/YAML 格式的 API 文档
            # 路径：/swagger.json 或 /swagger.yaml
            re_path(
                r"^swagger(?P<format>\.json|\.yaml)$",  # 正则匹配 swagger.json 或 swagger.yaml
                schema_view.without_ui(cache_timeout=0),  # 无 UI 的纯数据格式
                name="schema-json",  # URL 名称，用于反向解析
            ),
            
            # Swagger UI 界面 - 交互式 API 文档
            # 路径：/ (根路径)
            path(
                "",  # 根路径，访问首页时显示 Swagger 文档
                schema_view.with_ui("swagger", cache_timeout=0),  # 带 Swagger UI 界面
                name="schema-swagger-ui",
            ),
            
            # ReDoc UI 界面 - 另一种 API 文档展示方式
            # 路径：/redoc/
            path(
                r"redoc/",
                schema_view.with_ui("redoc", cache_timeout=0),  # 带 ReDoc UI 界面
                name="schema-redoc",
            ),

            # ============= 系统核心 API 路由 =============
            # 系统管理相关的所有 API 接口
            # 路径：/api/system/* (包含用户、角色、权限、菜单等管理接口)
            path("api/system/", include("dvadmin.system.urls")),

            # ============= 认证相关路由 =============
            # 用户登录接口 - 获取访问令牌
            # 路径：/api/login/
            path("api/login/", LoginView.as_view(), name="token_obtain_pair"),
            
            # 用户登出接口 - 注销当前会话
            # 路径：/api/logout/
            path("api/logout/", LogoutView.as_view(), name="token_logout"),
            
            # JWT 令牌刷新接口 - 使用 refresh token 获取新的 access token
            # 路径：/token/refresh/
            path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

            # ============= REST Framework 内置认证 =============
            # Django REST Framework 提供的认证相关页面
            # 路径：/api-auth/* (包含登录、登出页面)
            re_path(
                r"^api-auth/", 
                include("rest_framework.urls", namespace="rest_framework")
            ),

            # ============= 系统功能接口 =============
            # 验证码生成接口 - 用于登录时的图形验证码
            # 路径：/api/captcha/
            path("api/captcha/", CaptchaView.as_view()),
            
            # 数据字典初始化接口 - 系统启动时初始化字典数据
            # 路径：/api/init/dictionary/
            path("api/init/dictionary/", InitDictionaryViewSet.as_view()),
            
            # 系统设置初始化接口 - 系统启动时初始化配置数据
            # 路径：/api/init/settings/
            path("api/init/settings/", InitSettingsViewSet.as_view()),
            
            # API 登录页面 - 用于 Swagger 文档的登录认证
            # 路径：/apiLogin/
            path("apiLogin/", ApiLogin.as_view()),

            # ============= 开发调试接口 =============
            # 开发环境专用的令牌获取接口
            # 警告：仅用于开发环境，生产环境必须关闭！
            # 路径：/api/token/
            path("api/token/", LoginTokenView.as_view()),

            # ============= 前端页面路由 =============
            # 前端 Vue3 应用主页
            # 路径：/web/
            path('web/', web_view, name='web_view'),
            
            # 前端静态文件服务（开发环境使用）
            # 路径：/web/<任意路径>
            path('web/<path:filename>', serve_web_files, name='serve_web_files'),
        ]
        
        # ============= 静态文件路由配置 =============
        # 媒体文件路由 - 用户上传的文件访问
        # 路径：/media/* -> settings.MEDIA_ROOT 目录
        + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
        
        # 静态资源文件路由 - CSS、JS、图片等静态资源
        # 路径：/static/* -> settings.STATIC_URL 目录  
        + static(settings.STATIC_URL, document_root=settings.STATIC_URL)
        
        # ============= 动态插件路由 =============
        # 根据 settings.PLUGINS_URL_PATTERNS 动态加载插件路由
        # 支持插件系统的 URL 扩展，实现插件化架构
        + [
            re_path(ele.get('re_path'), include(ele.get('include'))) 
            for ele in settings.PLUGINS_URL_PATTERNS
        ]
)

# ================================================= #
# ******************** 路由说明总结 ***************** #
# ================================================= #

"""
URL 路由总结：

1. **API 文档访问**：
   - GET / -> Swagger UI 文档
   - GET /redoc/ -> ReDoc 文档
   - GET /swagger.json -> JSON 格式 API 规范

2. **认证相关**：
   - POST /api/login/ -> 用户登录
   - POST /api/logout/ -> 用户登出
   - POST /token/refresh/ -> 刷新 JWT 令牌

3. **系统管理**：
   - /api/system/* -> 用户、角色、权限等管理接口
   - GET /api/captcha/ -> 获取验证码

4. **前端应用**：
   - GET /web/ -> 前端应用主页
   - GET /web/<path> -> 前端静态资源

5. **开发调试**：
   - POST /api/token/ -> 开发环境令牌获取（生产环境需关闭）

6. **静态文件**：
   - /media/* -> 用户上传文件
   - /static/* -> 系统静态资源

7. **插件扩展**：
   - 动态路由支持插件系统扩展
"""
