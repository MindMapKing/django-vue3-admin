# -*- coding: utf-8 -*-
"""
Django数据初始化基类模块

此模块提供了一个用于Django应用数据初始化的基类CoreInitialize。
主要功能：
1. 从JSON文件读取初始化数据
2. 使用Django REST Framework的序列化器进行数据验证和保存
3. 支持数据重置功能
4. 处理多对多关系字段
5. 提供灵活的数据过滤和去重机制

使用方法：
    继承CoreInitialize类，重写run方法，在run方法中调用save或init_base进行数据初始化

作者：Django Vue3 Admin项目组
"""

import json  # 用于解析JSON格式的初始化数据文件
import os    # 用于文件路径操作

from django.apps import apps  # 用于获取Django应用配置信息
from rest_framework import request  # REST framework的请求对象

from application import settings  # 项目配置文件
from dvadmin.system.models import Users  # 用户模型，用于设置默认创建者


class CoreInitialize:
    """
    数据初始化基类
    
    使用方法：继承此类，重写run方法，在run中调用save或init_base进行数据初始化
    
    主要特性：
    - 支持从JSON文件自动加载初始化数据
    - 支持数据重置功能（清空现有数据重新初始化）
    - 自动处理多对多关系字段
    - 使用DRF序列化器进行数据验证
    - 支持自定义唯一字段过滤
    """
    
    # 类属性默认值
    creator_id = None  # 创建者ID，用于记录数据创建人
    reset = False      # 是否重置数据标志
    request = request  # REST framework请求对象
    file_path = None   # JSON数据文件路径

    def __init__(self, reset=False, creator_id=None, app=None):
        """
        初始化方法
        
        Args:
            reset (bool): 是否重置初始化数据，True表示清空现有数据重新初始化
            creator_id (int): 创建人ID，用于记录数据创建者
            app (str): Django应用名称，用于定位数据文件路径
        """
        # 设置实例属性，优先使用传入参数，否则使用类属性默认值
        self.reset = reset or self.reset
        self.creator_id = creator_id or self.creator_id  
        self.app = app or ''  # 应用名称，用于构建数据文件路径
        
        # 设置请求对象的用户为系统中最早创建的用户（通常是超级管理员）
        # 这样可以确保初始化的数据有合法的创建者
        self.request.user = Users.objects.order_by('create_datetime').first()

    def init_base(self, Serializer, unique_fields=None):
        """
        基础初始化方法，从JSON文件读取数据并使用序列化器进行初始化
        
        Args:
            Serializer: DRF序列化器类，用于数据验证和保存
            unique_fields (list): 唯一字段列表，用于过滤重复数据
                                如果指定，则只使用这些字段进行重复检查
                                如果不指定，则使用所有非空非列表字段进行检查
        
        工作流程：
        1. 根据序列化器的模型名称构建JSON文件路径
        2. 读取JSON文件中的数据
        3. 根据unique_fields或所有字段构建过滤条件
        4. 检查数据库中是否已存在相同数据
        5. 使用序列化器验证并保存数据
        """
        # 获取序列化器关联的模型类
        model = Serializer.Meta.model
        
        # 构建JSON数据文件路径
        # 路径格式：应用目录/fixtures/init_模型名.json
        path_file = os.path.join(
            apps.get_app_config(self.app.split('.')[-1]).path,  # 获取应用路径
            'fixtures',  # fixtures目录
            f'init_{Serializer.Meta.model._meta.model_name}.json'  # JSON文件名
        )
        
        # 检查文件是否存在
        if not os.path.isfile(path_file):
            print("文件不存在，跳过初始化")
            return
            
        # 读取并处理JSON数据文件
        with open(path_file, encoding="utf-8") as f:
            # 遍历JSON文件中的每条数据记录
            for data in json.load(f):
                filter_data = {}  # 用于数据库查询的过滤条件
                
                # 构建过滤条件
                if unique_fields:
                    # 如果指定了唯一字段，只使用这些字段作为过滤条件
                    for field in unique_fields:
                        if field in data:
                            filter_data[field] = data[field]
                else:
                    # 如果没有指定唯一字段，使用所有有效字段作为过滤条件
                    for key, value in data.items():
                        # 跳过列表类型、None值和空字符串
                        if isinstance(value, list) or value == None or value == '':
                            continue
                        filter_data[key] = value
                
                # 根据过滤条件查询数据库中是否已存在相同记录
                instance = model.objects.filter(**filter_data).first()
                
                # 添加重置标志到数据中
                data["reset"] = self.reset
                
                # 使用序列化器进行数据验证和保存
                # 如果instance存在则更新，否则创建新记录
                serializer = Serializer(instance, data=data, request=self.request)
                serializer.is_valid(raise_exception=True)  # 验证数据，出错时抛出异常
                serializer.save()  # 保存数据到数据库
                
        # 打印初始化完成信息
        print(f"[{self.app}][{model._meta.model_name}]初始化完成")

    def save(self, obj, data: list, name=None, no_reset=False):
        """
        保存数据到数据库的通用方法
        
        Args:
            obj: Django模型类，要保存数据的目标模型
            data (list): 要保存的数据列表，每个元素是一个字典
            name (str): 显示名称，用于日志输出，默认使用模型的verbose_name
            no_reset (bool): 是否禁用重置功能，True表示不清空现有数据
        
        功能特性：
        - 支持数据重置（清空现有数据）
        - 自动处理多对多关系字段
        - 使用get_or_create避免重复数据
        - 智能合并多对多关系数据
        """
        # 设置显示名称，默认使用模型的verbose_name
        name = name or obj._meta.verbose_name
        print(f"正在初始化[{obj._meta.label} => {name}]")
        
        # 数据重置逻辑
        if not no_reset and self.reset and obj not in settings.INITIALIZE_RESET_LIST:
            try:
                # 删除模型的所有数据
                obj.objects.all().delete()
                # 将模型添加到已重置列表，避免重复重置
                settings.INITIALIZE_RESET_LIST.append(obj)
            except Exception:
                # 如果删除失败（可能由于外键约束），静默处理
                pass
        
        # 遍历数据列表，逐个处理每条记录
        for ele in data:
            m2m_dict = {}    # 存储多对多关系字段
            new_data = {}    # 存储普通字段
            
            # 分离多对多字段和普通字段
            for key, value in ele.items():
                # 判断是否为多对多字段：值是列表且第一个元素是整数
                if isinstance(value, list) and value and isinstance(value[0], int):
                    m2m_dict[key] = value  # 多对多字段
                else:
                    new_data[key] = value  # 普通字段
            
            # 使用get_or_create获取或创建对象
            # 如果ID存在则获取，否则使用defaults创建新对象
            object, _ = obj.objects.get_or_create(id=ele.get("id"), defaults=new_data)
            
            # 处理多对多关系字段
            for key, m2m in m2m_dict.items():
                m2m = list(set(m2m))  # 去重
                # 如果多对多数据非空且有效
                if m2m and len(m2m) > 0 and m2m[0]:
                    # 使用exec动态执行代码，合并现有的多对多关系
                    exec(f"""
if object.{key}:
    # 获取现有的多对多关系ID列表
    values_list = object.{key}.all().values_list('id', flat=True)
    # 合并现有ID和新ID，并去重
    values_list = list(set(list(values_list) + {m2m}))
    # 设置新的多对多关系
    object.{key}.set(values_list)
""")
        
        # 打印初始化完成信息
        print(f"初始化完成[{obj._meta.label} => {name}]")

    def run(self):
        """
        抽象方法，子类必须重写此方法
        
        在此方法中调用save()或init_base()方法进行具体的数据初始化操作
        
        Raises:
            NotImplementedError: 如果子类没有重写此方法
        """
        raise NotImplementedError('.run() must be overridden')
