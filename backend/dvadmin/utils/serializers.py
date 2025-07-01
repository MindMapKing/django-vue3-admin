# -*- coding: utf-8 -*-

"""
Django REST Framework自定义序列化器模块

此模块提供了增强版的ModelSerializer，主要功能：
1. 自动处理审计字段（创建人、修改人、时间戳等）
2. 支持动态字段过滤
3. 自动设置数据所属部门
4. 提供友好的错误信息显示
5. 集成请求上下文信息

主要特性：
- 继承DRF的ModelSerializer，保持原有功能
- 集成DynamicFieldsMixin，支持动态字段选择
- 自动记录操作用户信息
- 统一的时间格式化
- 中文友好的错误提示

@author: 猿小天
@contact: QQ:1638245306
@Created on: 2021/6/1 001 22:47
@Remark: 自定义序列化器
"""
from rest_framework import serializers  # DRF序列化器基础组件
from rest_framework.fields import empty  # DRF空值常量
from rest_framework.request import Request  # DRF请求对象类型
from rest_framework.serializers import ModelSerializer  # DRF模型序列化器基类
from django.utils.functional import cached_property  # Django缓存属性装饰器
from rest_framework.utils.serializer_helpers import BindingDict  # DRF字段绑定字典

from dvladmin.system.models import Users  # 用户模型，用于获取用户信息
from django_restql.mixins import DynamicFieldsMixin  # 动态字段混入类


class CustomModelSerializer(DynamicFieldsMixin, ModelSerializer):
    """
    增强版DRF ModelSerializer序列化器
    
    主要增强功能：
    1. 自动更新模型的审计字段记录（创建人、修改人、时间戳）
    2. 支持动态字段过滤（通过DynamicFieldsMixin）
    3. 自动设置数据所属部门
    4. 提供友好的错误信息显示
    5. 集成请求上下文，可通过self.request获取Request对象
    
    使用方法：
        继承此类替代DRF的ModelSerializer，自动获得审计功能
        
    审计字段说明：
        - creator: 创建人字段，记录数据创建者
        - modifier: 修改人字段，记录数据最后修改者
        - create_datetime: 创建时间字段
        - update_datetime: 更新时间字段
        - dept_belong_id: 数据所属部门字段
    """

    # ==================== 审计字段配置 ====================
    # 修改人的审计字段名称, 默认"modifier", 继承使用时可自定义覆盖
    modifier_field_id = "modifier"
    # 修改人姓名字段，只读，通过方法动态获取
    modifier_name = serializers.SerializerMethodField(read_only=True)

    def get_modifier_name(self, instance):
        """
        获取修改人姓名的方法
        
        Args:
            instance: 模型实例对象
            
        Returns:
            str: 修改人姓名，如果不存在返回None
        """
        # 检查实例是否有modifier字段
        if not hasattr(instance, "modifier"):
            return None
            
        # 根据modifier ID查询用户姓名
        queryset = (
            Users.objects.filter(id=instance.modifier)
            .values_list("name", flat=True)  # 只获取name字段，返回扁平列表
            .first()  # 获取第一个结果
        )
        if queryset:
            return queryset
        return None

    # 创建人的审计字段名称, 默认"creator", 继承使用时可自定义覆盖
    creator_field_id = "creator"
    # 创建人姓名字段，通过SlugRelatedField关联到用户的name字段
    creator_name = serializers.SlugRelatedField(
        slug_field="name",    # 关联字段名
        source="creator",     # 数据源字段
        read_only=True       # 只读字段
    )
    
    # ==================== 部门字段配置 ====================
    # 数据所属部门字段名称
    dept_belong_id_field_name = "dept_belong_id"
    
    # ==================== 时间字段格式化 ====================
    # 添加默认时间返回格式，统一时间显示格式
    create_datetime = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S",  # 时间格式：年-月-日 时:分:秒
        required=False,               # 非必填字段
        read_only=True               # 只读字段，不允许客户端修改
    )
    update_datetime = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S",  # 时间格式：年-月-日 时:分:秒
        required=False,               # 非必填字段
        read_only=True               # 只读字段，不允许客户端修改
    )

    def __init__(self, instance=None, data=empty, request=None, **kwargs):
        """
        序列化器初始化方法
        
        Args:
            instance: 模型实例，用于更新操作
            data: 输入数据，用于创建或更新
            request: HTTP请求对象，用于获取用户信息
            **kwargs: 其他参数
        """
        # 调用父类初始化方法
        super().__init__(instance, data, **kwargs)
        # 设置请求对象，优先使用传入的request，否则从context中获取
        self.request: Request = request or self.context.get("request", None)

    def save(self, **kwargs):
        """
        保存方法，调用父类的save方法
        
        Args:
            **kwargs: 额外的保存参数
            
        Returns:
            保存后的模型实例
        """
        return super().save(**kwargs)

    def create(self, validated_data):
        """
        创建新对象的方法，自动设置审计字段
        
        Args:
            validated_data (dict): 验证后的数据
            
        Returns:
            创建的模型实例
            
        自动设置的字段：
        - modifier: 设置为当前请求用户ID
        - creator: 设置为当前请求用户对象
        - dept_belong_id: 设置为当前用户所属部门ID（如果未指定）
        """
        if self.request:
            # 检查用户是否已认证（不是匿名用户）
            if str(self.request.user) != "AnonymousUser":
                # 设置修改人字段
                if self.modifier_field_id in self.fields.fields:
                    validated_data[self.modifier_field_id] = self.get_request_user_id()
                # 设置创建人字段
                if self.creator_field_id in self.fields.fields:
                    validated_data[self.creator_field_id] = self.request.user

                # 设置数据所属部门字段（如果未指定且字段存在）
                if (
                        self.dept_belong_id_field_name in self.fields.fields
                        and validated_data.get(self.dept_belong_id_field_name, None) is None
                ):
                    # 使用当前用户的部门ID，如果用户没有部门则保持原值
                    validated_data[self.dept_belong_id_field_name] = getattr(
                        self.request.user, "dept_id", 
                        validated_data.get(self.dept_belong_id_field_name, None)
                    )
        # 调用父类的create方法执行实际创建
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        更新对象的方法，自动设置修改人字段
        
        Args:
            instance: 要更新的模型实例
            validated_data (dict): 验证后的数据
            
        Returns:
            更新后的模型实例
            
        自动设置的字段：
        - modifier: 设置为当前请求用户ID
        """
        if self.request:
            # 检查用户是否已认证（不是匿名用户）
            if str(self.request.user) != "AnonymousUser":
                # 在验证数据中设置修改人字段
                if self.modifier_field_id in self.fields.fields:
                    validated_data[self.modifier_field_id] = self.get_request_user_id()
            # 直接在实例上设置修改人字段（确保字段被更新）
            if hasattr(self.instance, self.modifier_field_id):
                setattr(
                    self.instance, self.modifier_field_id, self.get_request_user_id()
                )
        # 调用父类的update方法执行实际更新
        return super().update(instance, validated_data)

    # ==================== 用户信息获取方法 ====================
    def get_request_username(self):
        """
        获取当前请求用户的用户名
        
        Returns:
            str: 用户名，如果获取不到返回None
        """
        if getattr(self.request, "user", None):
            return getattr(self.request.user, "username", None)
        return None

    def get_request_name(self):
        """
        获取当前请求用户的姓名
        
        Returns:
            str: 用户姓名，如果获取不到返回None
        """
        if getattr(self.request, "user", None):
            return getattr(self.request.user, "name", None)
        return None

    def get_request_user_id(self):
        """
        获取当前请求用户的ID
        
        Returns:
            int: 用户ID，如果获取不到返回None
        """
        if getattr(self.request, "user", None):
            return getattr(self.request.user, "id", None)
        return None

    @property
    def errors(self):
        """
        重写errors属性，提供更友好的错误信息显示
        
        将字段名替换为模型字段的verbose_name（中文名称），
        使错误信息更易于理解
        
        Returns:
            dict: 包含友好字段名的错误信息字典
        """
        # 获取父类的错误信息
        errors = super().errors
        verbose_errors = {}

        # 构建字段名到verbose_name的映射字典
        # 格式：{ field.name: field.verbose_name } 用于每个有verbose_name的字段
        fields = {field.name: field.verbose_name for field in
                  self.Meta.model._meta.get_fields() if hasattr(field, 'verbose_name')}

        # 遍历错误信息，将字段名替换为中文名称
        for field_name, error in errors.items():
            if field_name in fields:
                # 使用中文字段名作为错误信息的键
                verbose_errors[str(fields[field_name])] = error
            else:
                # 如果没有中文名称，保持原字段名
                verbose_errors[field_name] = error
        return verbose_errors

    # ==================== 动态字段过滤功能（已注释） ====================
    # 以下代码实现了动态字段过滤功能，但当前被注释掉
    # 功能说明：通过URL参数_fields和_exclude来动态选择返回的字段
    # 
    # @cached_property
    # def fields(self):
    #     """
    #     动态字段过滤功能
    #     
    #     支持通过URL参数控制返回字段：
    #     - _fields: 指定要包含的字段，用逗号分隔
    #     - _exclude: 指定要排除的字段，用逗号分隔
    #     
    #     示例：
    #     /api/users/?_fields=id,name,email  # 只返回id、name、email字段
    #     /api/users/?_exclude=password      # 排除password字段
    #     """
    #     # 获取所有字段的绑定字典
    #     fields = BindingDict(self)
    #     for key, value in self.get_fields().items():
    #         fields[key] = value
    #
    #     # 检查是否有上下文
    #     if not hasattr(self, '_context'):
    #         return fields
    #     
    #     # 检查是否为根序列化器或列表根序列化器
    #     is_root = self.root == self
    #     parent_is_list_root = self.parent == self.root and getattr(self.parent, 'many', False)
    #     if not (is_root or parent_is_list_root):
    #         return fields
    #
    #     try:
    #         # 获取请求对象
    #         request = self.request or self.context['request']
    #     except KeyError:
    #         return fields
    #     
    #     # 获取查询参数
    #     params = getattr(
    #         request, 'query_params', getattr(request, 'GET', None)
    #     )
    #     if params is None:
    #         pass
    #     
    #     try:
    #         # 解析_fields参数（要包含的字段）
    #         filter_fields = params.get('_fields', None).split(',')
    #     except AttributeError:
    #         filter_fields = None
    #
    #     try:
    #         # 解析_exclude参数（要排除的字段）
    #         omit_fields = params.get('_exclude', None).split(',')
    #     except AttributeError:
    #         omit_fields = []
    #
    #     # 获取现有字段集合
    #     existing = set(fields.keys())
    #     if filter_fields is None:
    #         allowed = existing  # 如果没有指定_fields，允许所有字段
    #     else:
    #         allowed = set(filter(None, filter_fields))  # 过滤空值
    #
    #     omitted = set(filter(None, omit_fields))  # 要排除的字段集合
    #     
    #     # 应用字段过滤规则
    #     for field in existing:
    #         if field not in allowed:
    #             fields.pop(field, None)  # 移除不在允许列表中的字段
    #         if field in omitted:
    #             fields.pop(field, None)  # 移除在排除列表中的字段
    #
    #     return fields
