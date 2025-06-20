# -*- coding: utf-8 -*-
"""
WebSocket 路由配置文件

该文件定义了 Django Channels 框架中的 WebSocket 路由规则，
用于处理客户端与服务器之间的实时双向通信连接。

主要功能：
1. 配置 WebSocket 连接的 URL 路径
2. 将特定路径的连接请求路由到对应的消费者（Consumer）
3. 支持动态路径参数，实现个性化连接管理
"""

# 导入 Django 的路径配置模块
from django.urls import path
# 导入自定义的 WebSocket 消费者类
from application.websocketConfig import MegCenter

# WebSocket URL 路由配置列表
# 定义所有 WebSocket 连接的路由规则
websocket_urlpatterns = [
    # WebSocket 连接路由配置
    # 路径格式: ws/<service_uid>/
    # - ws/: WebSocket 连接的固定前缀
    # - <str:service_uid>: 动态路径参数，用于标识用户身份或服务标识符
    #   通常是经过 JWT 编码的用户信息，用于身份验证和连接管理
    # - MegCenter.as_asgi(): 将消息中心消费者类转换为 ASGI 应用
    #   MegCenter 继承自 DvadminWebSocket，负责处理消息推送和实时通信
    path('ws/<str:service_uid>/', MegCenter.as_asgi()),  # 消息中心 WebSocket 消费者路由
]

# 路由工作流程说明：
# 1. 客户端发起 WebSocket 连接请求到 ws/<token>/
# 2. Django Channels 根据 URL 模式匹配到对应的消费者
# 3. MegCenter 消费者处理连接建立、消息接收和推送
# 4. 通过 service_uid 参数进行用户身份验证和权限控制
# 5. 建立持久化连接，支持实时消息推送和双向通信
