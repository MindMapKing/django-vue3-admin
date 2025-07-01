# -*- coding: utf-8 -*-
"""
WebSocket 配置文件
================

该文件实现了Django-Vue3-Admin项目的WebSocket功能，主要用于：
1. 实时消息推送系统
2. 用户连接状态管理  
3. 消息中心集成
4. 多种消息推送方式（按用户、角色、部门推送）

依赖模块：
- Django Channels: 提供WebSocket支持
- JWT: 用于WebSocket连接身份验证
- Django ORM: 数据库操作
"""

import urllib

from asgiref.sync import sync_to_async, async_to_sync
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer, AsyncWebsocketConsumer
import json

from channels.layers import get_channel_layer
from jwt import InvalidSignatureError
from rest_framework.request import Request

from application import settings
from dvadmin.system.models import MessageCenter, Users, MessageCenterTargetUser
from dvadmin.system.views.message_center import MessageCenterTargetUserSerializer
from dvadmin.utils.serializers import CustomModelSerializer

# 全局变量：存储发送消息的字典结构
send_dict = {}


def set_message(sender, msg_type, msg, unread=0):
    """
    构建标准消息结构体
    
    Args:
        sender (str): 消息发送者标识
        msg_type (str): 消息类型（如：'SYSTEM', 'INFO', 'WARNING'等）
        msg (str): 消息内容
        unread (int): 未读消息数量，默认为0
    
    Returns:
        dict: 标准化的消息字典结构
        
    消息结构说明：
    - sender: 标识消息来源，便于前端区分处理
    - contentType: 消息类型，前端可据此设置不同样式
    - content: 实际消息内容
    - unread: 未读消息计数，用于前端显示红点提醒
    """
    text = {
        'sender': sender,           # 消息发送者
        'contentType': msg_type,    # 消息类型
        'content': msg,             # 消息内容
        'unread': unread           # 未读消息数量
    }
    return text


@database_sync_to_async
def _get_message_center_instance(message_id):
    """
    异步获取消息中心的目标用户列表
    
    该函数用于查询特定消息ID对应的目标用户列表，
    支持异步操作以避免阻塞WebSocket连接。
    
    Args:
        message_id (int): 消息中心消息ID
        
    Returns:
        QuerySet: 目标用户ID列表，如果消息不存在则返回空列表
        
    注意：
    - 使用@database_sync_to_async装饰器将同步数据库操作转换为异步
    - 只返回用户ID列表，减少数据传输量
    """
    from dvadmin.system.models import MessageCenter
    # 查询指定消息ID的目标用户列表，只获取用户ID
    _MessageCenter = MessageCenter.objects.filter(id=message_id).values_list('target_user', flat=True)
    if _MessageCenter:
        return _MessageCenter
    else:
        return []


@database_sync_to_async
def _get_message_unread(user_id):
    """
    异步获取用户的未读消息数量
    
    该函数统计指定用户的未读消息总数，
    用于在用户连接时显示未读消息提醒。
    
    Args:
        user_id (int): 用户ID
        
    Returns:
        int: 未读消息数量，如果没有未读消息则返回0
        
    业务逻辑：
    - 查询MessageCenterTargetUser表中is_read=False的记录
    - 按用户ID过滤
    - 返回记录总数
    """
    from dvadmin.system.models import MessageCenterTargetUser
    # 统计指定用户的未读消息数量
    count = MessageCenterTargetUser.objects.filter(users=user_id, is_read=False).count()
    return count or 0


def request_data(scope):
    """
    从WebSocket连接的scope中解析查询参数
    
    WebSocket连接建立时，客户端可以通过URL查询参数传递数据，
    该函数负责解析这些参数。
    
    Args:
        scope (dict): WebSocket连接的作用域对象，包含连接信息
        
    Returns:
        dict: 解析后的查询参数字典
        
    处理流程：
    1. 从scope中获取query_string（二进制格式）
    2. 解码为UTF-8字符串
    3. 使用urllib.parse.parse_qs解析为字典
    
    示例：
    URL: ws://localhost:8000/ws/socket/token123/?param1=value1&param2=value2
    返回: {'param1': ['value1'], 'param2': ['value2']}
    """
    # 获取查询字符串（二进制格式）并解码为UTF-8
    query_string = scope.get('query_string', b'').decode('utf-8')
    # 解析查询字符串为字典格式
    qs = urllib.parse.parse_qs(query_string)
    return qs


class DvdadminWebSocket(AsyncJsonWebsocketConsumer):
    """
    DVAdmin WebSocket 基础消费者类
    
    这是所有WebSocket功能的基础类，提供：
    1. JWT身份验证
    2. 用户连接管理
    3. 消息推送基础功能
    4. 连接状态维护
    
    继承自AsyncJsonWebsocketConsumer，支持JSON格式消息的异步处理。
    """
    
    async def connect(self):
        """
        处理WebSocket连接建立
        
        连接建立流程：
        1. 从URL路径中提取JWT令牌
        2. 验证JWT令牌的有效性
        3. 提取用户ID并创建用户分组
        4. 将连接加入到对应的用户分组
        5. 发送连接成功消息和未读消息提醒
        
        异常处理：
        - JWT令牌无效时自动断开连接
        """
        try:
            import jwt
            # 从URL路径参数中获取JWT令牌
            # URL格式: /ws/socket/{service_uid}/
            self.service_uid = self.scope["url_route"]["kwargs"]["service_uid"]
            
            # 使用Django的SECRET_KEY验证JWT令牌
            decoded_result = jwt.decode(self.service_uid, settings.SECRET_KEY, algorithms=["HS256"])
            
            if decoded_result:
                # 从JWT载荷中提取用户ID
                self.user_id = decoded_result.get('user_id')
                # 创建用户专属的频道分组名称
                # 格式: "user_{用户ID}"
                self.chat_group_name = "user_" + str(self.user_id)
                
                # 将当前连接加入到用户分组中
                # 这样可以向该用户的所有连接发送消息
                await self.channel_layer.group_add(
                    self.chat_group_name,    # 分组名称
                    self.channel_name        # 当前连接的频道名称
                )
                
                # 接受WebSocket连接
                await self.accept()
                
                # 获取用户的未读消息数量
                unread_count = await _get_message_unread(self.user_id)
                
                if unread_count == 0:
                    # 如果没有未读消息，发送简单的上线通知
                    await self.send_json(set_message('system', 'SYSTEM', '您已上线'))
                else:
                    # 如果有未读消息，发送带有未读消息计数的提醒
                    await self.send_json(
                        set_message('system', 'SYSTEM', "请查看您的未读消息~",
                                    unread=unread_count))
        except InvalidSignatureError:
            # JWT令牌验证失败，断开连接
            await self.disconnect(None)

    async def disconnect(self, close_code):
        """
        处理WebSocket连接断开
        
        断开连接流程：
        1. 从用户分组中移除当前连接
        2. 记录连接关闭日志
        3. 清理连接资源
        
        Args:
            close_code: 连接关闭代码，可能为None（主动断开）
        """
        # 从用户分组中移除当前连接
        await self.channel_layer.group_discard(self.chat_group_name, self.channel_name)
        print("连接关闭")
        
        try:
            # 关闭WebSocket连接
            await self.close(close_code)
        except Exception:
            # 忽略关闭过程中的异常
            pass


class MegCenter(DvdadminWebSocket):
    """
    消息中心WebSocket消费者
    
    专门处理消息中心相关的WebSocket功能：
    1. 接收客户端发送的消息推送请求
    2. 根据消息配置向目标用户推送消息
    3. 支持群发消息功能
    
    继承自DvdadminWebSocket，拥有基础的连接管理功能。
    """

    async def receive(self, text_data):
        """
        接收并处理客户端发送的消息
        
        客户端可以发送包含message_id的JSON消息，
        服务器会根据该消息ID查找目标用户并推送消息。
        
        Args:
            text_data (str): 客户端发送的JSON字符串
            
        消息格式示例：
        {
            "message_id": 123,
            "content": "消息内容",
            "type": "INFO"
        }
        
        处理流程：
        1. 解析JSON消息
        2. 提取消息ID
        3. 查询消息的目标用户列表
        4. 向所有目标用户推送消息
        """
        # 解析客户端发送的JSON消息
        text_data_json = json.loads(text_data)
        
        # 提取消息ID，如果没有则为None
        message_id = text_data_json.get('message_id', None)
        
        # 根据消息ID查询目标用户列表
        user_list = await _get_message_center_instance(message_id)
        
        # 向每个目标用户推送消息
        for send_user in user_list:
            await self.channel_layer.group_send(
                "user_" + str(send_user),           # 目标用户的分组名称
                {'type': 'push.message', 'json': text_data_json}  # 消息类型和内容
            )

    async def push_message(self, event):
        """
        实际的消息推送方法
        
        该方法由channel_layer.group_send调用，
        负责将消息发送给WebSocket客户端。
        
        Args:
            event (dict): 包含消息数据的事件字典
                - type: 消息类型（'push.message'）
                - json: 要发送的JSON数据
        
        注意：
        - 方法名必须与group_send中的type参数对应
        - 'push.message' 对应方法名 'push_message'（用下划线替换点号）
        """
        # 从事件中提取消息数据
        message = event['json']
        # 将消息发送给WebSocket客户端
        await self.send(text_data=json.dumps(message))


class MessageCreateSerializer(CustomModelSerializer):
    """
    消息中心创建序列化器
    
    用于验证和创建消息中心记录的序列化器。
    继承自CustomModelSerializer，提供了标准的
    数据验证和序列化功能。
    
    用途：
    - 验证消息创建时的数据格式
    - 将验证后的数据保存到数据库
    - 提供一致的API接口
    """
    class Meta:
        model = MessageCenter          # 对应的数据模型
        fields = "__all__"            # 包含所有字段
        read_only_fields = ["id"]     # ID字段为只读，自动生成


def websocket_push(user_id, message):
    """
    WebSocket消息推送工具函数
    
    这是一个同步函数，可以在Django视图、信号处理器等
    同步代码中调用，用于向特定用户推送WebSocket消息。
    
    Args:
        user_id (int): 目标用户ID
        message (dict): 要推送的消息字典
        
    使用场景：
    - 在Django视图中推送即时通知
    - 在信号处理器中推送状态更新
    - 在定时任务中推送提醒消息
    
    实现原理：
    - 使用async_to_sync将异步的group_send转换为同步调用
    - 通过channel_layer向用户分组发送消息
    """
    # 构造用户分组名称
    username = "user_" + str(user_id)
    
    # 获取Channel Layer实例
    channel_layer = get_channel_layer()
    
    # 同步调用异步的group_send方法
    async_to_sync(channel_layer.group_send)(
        username,                    # 目标分组
        {
            "type": "push.message",  # 消息类型
            "json": message         # 消息内容
        }
    )


def create_message_push(title: str, content: str, target_type: int = 0, target_user: list = None, target_dept=None,
                        target_role=None, message: dict = None, request=Request):
    """
    创建消息并推送给目标用户
    
    这是消息系统的核心函数，负责：
    1. 创建消息记录到消息中心
    2. 根据推送类型确定目标用户
    3. 创建用户-消息关联记录
    4. 向所有目标用户推送WebSocket消息
    
    Args:
        title (str): 消息标题
        content (str): 消息内容
        target_type (int): 推送类型
            - 0: 指定用户推送（默认）
            - 1: 按角色推送
            - 2: 按部门推送  
            - 3: 系统通知（全员推送）
        target_user (list): 目标用户ID列表（target_type=0时使用）
        target_dept (list): 目标部门ID列表（target_type=2时使用）
        target_role (list): 目标角色ID列表（target_type=1时使用）
        message (dict): 自定义消息格式，默认为INFO类型
        request (Request): Django请求对象，用于序列化器上下文
        
    推送流程：
    1. 参数预处理和默认值设置
    2. 创建消息中心记录
    3. 根据推送类型查询目标用户
    4. 创建用户-消息关联记录
    5. 向每个目标用户推送WebSocket消息（包含未读计数）
    
    异常处理：
    - 数据验证失败时抛出ValidationError
    - 数据库操作失败时向上传播异常
    """
    # 设置默认消息格式
    if message is None:
        message = {"contentType": "INFO", "content": None}
    
    # 设置默认的目标列表（避免可变默认参数问题）
    if target_role is None:
        target_role = []
    if target_dept is None:
        target_dept = []
    
    # 构造消息数据
    data = {
        "title": title,              # 消息标题
        "content": content,          # 消息内容  
        "target_type": target_type,  # 推送类型
        "target_user": target_user,  # 目标用户列表
        "target_dept": target_dept,  # 目标部门列表
        "target_role": target_role   # 目标角色列表
    }
    
    # 创建并验证消息中心记录
    message_center_instance = MessageCreateSerializer(data=data, request=request)
    message_center_instance.is_valid(raise_exception=True)  # 验证失败则抛出异常
    message_center_instance.save()  # 保存到数据库
    
    # 初始化目标用户列表
    users = target_user or []
    
    # 根据推送类型确定目标用户
    if target_type in [1]:  # 按角色推送
        # 查询指定角色下的所有用户
        users = Users.objects.filter(role__id__in=target_role).values_list('id', flat=True)
    if target_type in [2]:  # 按部门推送
        # 查询指定部门下的所有用户
        users = Users.objects.filter(dept__id__in=target_dept).values_list('id', flat=True)
    if target_type in [3]:  # 系统通知（全员推送）
        # 查询系统中的所有用户
        users = Users.objects.values_list('id', flat=True)
    
    # 构造用户-消息关联数据
    targetuser_data = []
    for user in users:
        targetuser_data.append({
            "messagecenter": message_center_instance.instance.id,  # 消息中心记录ID
            "users": user                                         # 用户ID
        })
    
    # 批量创建用户-消息关联记录
    targetuser_instance = MessageCenterTargetUserSerializer(data=targetuser_data, many=True, request=request)
    targetuser_instance.is_valid(raise_exception=True)  # 验证失败则抛出异常
    targetuser_instance.save()  # 保存到数据库
    
    # 向每个目标用户推送WebSocket消息
    for user in users:
        # 构造用户分组名称
        username = "user_" + str(user)
        
        # 获取用户当前的未读消息数量
        unread_count = async_to_sync(_get_message_unread)(user)
        
        # 获取Channel Layer实例
        channel_layer = get_channel_layer()
        
        # 推送消息到用户分组
        async_to_sync(channel_layer.group_send)(
            username,                                    # 目标用户分组
            {
                "type": "push.message",                 # 消息类型
                "json": {**message, 'unread': unread_count}  # 合并消息内容和未读计数
            }
        )
