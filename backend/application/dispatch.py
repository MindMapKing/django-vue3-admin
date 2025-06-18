#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置调度模块 (Configuration Dispatch Module)

该模块负责管理Django应用中的配置信息，包括：
1. 字典配置的初始化、获取和刷新
2. 系统配置的初始化、获取和刷新  
3. 多租户模式的支持
4. Redis缓存的支持

主要功能：
- 动态管理系统字典和配置数据
- 支持租户隔离的配置管理
- 提供配置的缓存机制
"""

# 导入Django核心组件
from django.conf import settings  # Django设置配置
from django.db import connection  # 数据库连接对象
from django.core.cache import cache  # Django缓存系统
from dvadmin.utils.validator import CustomValidationError  # 自定义验证异常

# 获取调度数据库类型配置，默认为内存模式，可选择redis模式
# 注意：DISPATCH_DB_TYPE配置项需要在以下位置之一进行配置：
# 1. backend/conf/env.py 文件中定义（推荐）
# 2. 环境变量中设置 DISPATCH_DB_TYPE=redis
# 3. 在settings.py中直接添加 DISPATCH_DB_TYPE = 'redis'
# 4. 在具体的环境配置文件中定义（如dev.py、prod.py等）
# 如果未配置此项，系统将使用默认的内存模式进行字典和配置数据缓存
dispatch_db_type = getattr(settings, 'DISPATCH_DB_TYPE', 'memory')  # redis


def is_tenants_mode():
    """
    判断当前是否为多租户模式
    
    多租户模式下，每个租户拥有独立的数据库schema，
    通过connection.tenant.schema_name来区分不同租户
    
    Returns:
        bool: True表示启用多租户模式，False表示单租户模式
    """
    # 检查数据库连接对象是否具有tenant属性（多租户模式标识）
    # 并验证tenant对象是否存在schema_name属性且不为空
    # connection.tenant是从数据库连接中获取的租户信息对象
    # schema_name是租户的数据库模式名称，用于标识不同租户的数据隔离
    return hasattr(connection, "tenant") and connection.tenant.schema_name


# ================================================= #
# ******************** 初始化模块 ******************** #
# ================================================= #

def _get_all_dictionary():
    """
    从数据库获取所有字典配置数据
    
    该函数查询Dictionary模型，获取所有启用状态且非值类型的字典项，
    构建包含父子关系的字典数据结构
    
    Returns:
        dict: 以字典value为key，包含id、value、children的字典对象
              children包含该字典下所有子项的label、value、type、color信息
    """
    from dvadmin.system.models import Dictionary

    # 查询所有启用且非值类型的字典项（父级字典）
    queryset = Dictionary.objects.filter(status=True, is_value=False)
    data = []
    
    # 遍历每个父级字典项
    # 在Python中，数组（列表）可以直接包含JSON对象（字典），这是Python的核心特性
    # 与Java不同，Python的列表可以存储任意类型的对象，包括字典、对象实例、函数等
    # 
    # 数据结构示例：
    # data = [
    #     {"id": 1, "value": "user_status", "children": [...]},
    #     {"id": 2, "value": "order_status", "children": [...]}
    # ]
    # 
    # 这种设计的优势：
    # 1. 灵活性：可以直接在列表中存储复杂的数据结构
    # 2. 易读性：代码结构清晰，直观表达数据关系
    # 3. 性能：避免了额外的序列化/反序列化开销
    # 4. 兼容性：生成的数据结构可以直接转换为JSON格式
    for instance in queryset:
        data.append(
            {
                "id": instance.id,  # 字典项ID
                "value": instance.value,  # 字典项值（用作key）
                # 获取该字典项下所有启用的子项
                "children": list(
                    Dictionary.objects.filter(parent=instance.id)  # 按父级ID过滤
                    .filter(status=1)  # 只获取启用状态的子项
                    .values("label", "value", "type", "color")  # 选择需要的字段
                ),
            }
        )
        
    # 返回以value为key的字典，方便后续快速查找
    # 使用字典推导式(Dictionary Comprehension)语法构建结果字典
    # 语法格式：{key_expression: value_expression for item in iterable}
    # 
    # 详细解析：
    # - ele.get("value"): 字典的键，从每个元素中获取"value"字段作为key
    # - ele: 字典的值，整个元素对象作为value
    # - for ele in data: 遍历data列表中的每个元素
    # 
    # 等价的传统写法：
    # result = {}
    # for ele in data:
    #     key = ele.get("value")
    #     result[key] = ele
    # return result
    #
    # 这种语法的优势：
    # 1. 代码更简洁，一行完成字典构建
    # 2. 性能更好，内部优化过的C实现
    # 3. 更符合Python的函数式编程风格
    return {ele.get("value"): ele for ele in data}


def _get_all_system_config():
    """
    从数据库获取所有系统配置数据
    
    该函数查询SystemConfig模型，获取所有子级配置项，
    构建以"父级key.子级key"为键的配置字典
    
    Returns:
        dict: 以"父级key.子级key"为键的系统配置字典
              根据不同的form_item_type处理不同类型的配置值
    """
    data = {}
    from dvladmin.system.models import SystemConfig

    # 查询所有有父级的配置项（子级配置），按排序字段排序
    # SystemConfig模型分析：
    # 1. SystemConfig不是继承自某个父类，而是使用自关联(Self-Referential)的设计模式
    # 2. parent_id是SystemConfig模型自身的一个字段，用于实现树形结构
    # 3. parent_id指向同一个SystemConfig表中的另一条记录的主键
    # 4. __isnull是Django ORM的字段查找操作符，不是方法
    #
    # 自关联模型设计说明：
    # - parent_id = models.ForeignKey('self', ...)  # 指向自身的外键
    # - 这种设计允许创建层级结构：父配置 -> 子配置
    # - parent_id为空的记录是顶级配置
    # - parent_id不为空的记录是子级配置
    #
    # Django ORM字段查找操作符大全：
    # 
    # 1. 空值判断操作符：
    # - __isnull=False: 查询parent_id字段不为空的记录
    # - __isnull=True: 查询parent_id字段为空的记录
    # 
    # 2. 精确匹配操作符：
    # - __exact: 精确匹配（默认，可省略）
    # - __iexact: 忽略大小写的精确匹配
    # 
    # 3. 包含操作符：
    # - __contains: 区分大小写的包含
    # - __icontains: 忽略大小写的包含
    # - __in: 在给定列表中
    # 
    # 4. 比较操作符：
    # - __gt: 大于
    # - __gte: 大于等于
    # - __lt: 小于
    # - __lte: 小于等于
    # 
    # 5. 模式匹配操作符：
    # - __startswith: 以...开头（区分大小写）
    # - __istartswith: 以...开头（忽略大小写）
    # - __endswith: 以...结尾（区分大小写）
    # - __iendswith: 以...结尾（忽略大小写）
    # - __regex: 正则表达式匹配（区分大小写）
    # - __iregex: 正则表达式匹配（忽略大小写）
    # 
    # 6. 日期时间操作符：
    # - __year: 年份
    # - __month: 月份
    # - __day: 日
    # - __hour: 小时
    # - __minute: 分钟
    # - __second: 秒
    # - __date: 日期部分
    # - __time: 时间部分
    # - __week_day: 星期几
    # - __range: 范围查询
    # 
    # 7. 关系查询操作符（用于外键）：
    # - 通过双下划线跨表查询，如：parent__key, parent__name
    # - 可以多层关联：category__parent__name
    # 
    # 使用示例：
    # SystemConfig.objects.filter(key__icontains='email')  # key包含'email'（忽略大小写）
    # SystemConfig.objects.filter(id__in=[1,2,3])  # id在列表中
    # SystemConfig.objects.filter(create_datetime__year=2023)  # 2023年创建的记录
    # SystemConfig.objects.filter(parent__key__startswith='sys')  # 父级key以'sys'开头
    # Django QuerySet链式调用的括号使用有以下几个重要作用：
    # 
    # 1. 代码可读性和格式化：
    #    - 使用括号可以将长的链式调用分成多行，每行一个方法调用
    #    - 便于阅读和理解每个操作的作用
    #    - 符合Python PEP 8代码规范中的行长度限制（建议不超过79字符）
    # 
    # 2. 避免续行符（反斜杠）：
    #    - 不使用括号时需要用反斜杠 \ 来续行，如：
    #      system_config_obj = SystemConfig.objects.filter(parent_id__isnull=False) \
    #                          .values("parent__key", "key", "value", "form_item_type") \
    #                          .order_by("sort")
    #    - 使用括号更简洁，不需要反斜杠
    # 
    # 3. Python语法特性：
    #    - 在括号、方括号、大括号内，Python会忽略换行符
    #    - 这被称为"隐式行连接"（implicit line joining）
    #    - 使代码更加Pythonic和优雅
    # 
    # 4. 团队协作优势：
    #    - 便于代码版本控制，每行修改更容易追踪
    #    - 便于代码审查，每个操作步骤清晰可见
    #    - 便于调试，可以注释单个操作而不影响其他部分
    # 
    # 两种写法功能完全相同：
    # 写法1（推荐）：使用括号多行
    system_config_obj = (
        SystemConfig.objects.filter(parent_id__isnull=False)  # 只查询子级配置（parent_id不为空）
        .values("parent__key", "key", "value", "form_item_type")  # 获取父级key、当前key、值、表单类型
        .order_by("sort")  # 按排序字段排序
    )
    
    # 写法2：单行（不推荐，太长）
    # system_config_obj = SystemConfig.objects.filter(parent_id__isnull=False).values("parent__key", "key", "value", "form_item_type").order_by("sort")
    
    # 遍历每个系统配置项
    for system_config in system_config_obj:
        value = system_config.get("value", "")  # 获取配置值
        
        # 处理文件上传类型配置(form_item_type=7)
        if value and system_config.get("form_item_type") == 7:
            value = value[0].get("url")  # 提取文件URL
            
        # 处理数组类型配置(form_item_type=11)    
        if value and system_config.get("form_item_type") == 11:
            new_value = []
            # 重新构建数组，确保包含key、title、value字段
            for ele in value:
                new_value.append({
                    "key": ele.get('key'),
                    "title": ele.get('title'),
                    "value": ele.get('value'),
                })
            # 按key字段排序
            # lambda表达式是Python中的匿名函数，用于创建简单的单行函数
            # 语法格式：lambda 参数: 表达式
            # 
            # 这行代码等价于定义一个函数：
            # def get_key(s):
            #     return s["key"]
            # new_value.sort(key=get_key)
            # 
            # Java中的等价写法：
            # 
            # 1. Java 8+的Lambda表达式写法：
            # newValue.sort((s1, s2) -> s1.get("key").compareTo(s2.get("key")));
            # 或者使用Comparator.comparing：
            # newValue.sort(Comparator.comparing(s -> s.get("key")));
            # 
            # 2. Java传统匿名内部类写法：
            # Collections.sort(newValue, new Comparator<Map<String, Object>>() {
            #     @Override
            #     public int compare(Map<String, Object> s1, Map<String, Object> s2) {
            #         return s1.get("key").toString().compareTo(s2.get("key").toString());
            #     }
            # });
            # 
            # Python的lambda更简洁，直接传入排序的取值函数
            # key=lambda s: s["key"] 表示：对每个元素s，使用s["key"]作为排序依据
            new_value.sort(key=lambda s: s["key"])
            value = new_value
            
        # 构建配置键名："父级key.子级key"
        data[f"{system_config.get('parent__key')}.{system_config.get('key')}"] = value
    
    return data


def init_dictionary():
    """
    初始化字典配置到缓存或内存
    
    根据dispatch_db_type配置决定使用Redis缓存还是内存存储
    支持多租户模式，为每个租户单独存储字典配置
    
    异常处理：
        如果数据库表不存在，会提示先进行数据库迁移
    """
    try:
        # 如果使用Redis缓存模式
        if dispatch_db_type == 'redis':
            cache.set(f"init_dictionary", _get_all_dictionary())
            return
            
        # 如果启用多租户模式
        if is_tenants_mode():
            from django_tenants.utils import tenant_context, get_tenant_model

            # 为每个租户单独初始化字典配置
            for tenant in get_tenant_model().objects.filter():
                with tenant_context(tenant):  # 切换到指定租户的数据库schema
                    # 将字典配置存储到settings中，以租户schema_name为key
                    settings.DICTIONARY_CONFIG[connection.tenant.schema_name] = _get_all_dictionary()
        else:
            # 单租户模式，直接存储到settings
            settings.DICTIONARY_CONFIG = _get_all_dictionary()
    except Exception as e:
        print("请先进行数据库迁移!")  # 提示用户先运行数据库迁移命令
    return


def init_system_config():
    """
    初始化系统配置到缓存或内存
    
    根据dispatch_db_type配置决定使用Redis缓存还是内存存储
    支持多租户模式，为每个租户单独存储系统配置
    
    异常处理：
        如果数据库表不存在，会提示先进行数据库迁移
    """
    try:
        # 如果使用Redis缓存模式
        if dispatch_db_type == 'redis':
            cache.set(f"init_system_config", _get_all_system_config())
            return
            
        # 如果启用多租户模式
        if is_tenants_mode():
            from django_tenants.utils import tenant_context, get_tenant_model

            # 为每个租户单独初始化系统配置
            for tenant in get_tenant_model().objects.filter():
                with tenant_context(tenant):  # 切换到指定租户的数据库schema
                    # 将系统配置存储到settings中，以租户schema_name为key
                    settings.SYSTEM_CONFIG[connection.tenant.schema_name] = _get_all_system_config()
        else:
            # 单租户模式，直接存储到settings
            settings.SYSTEM_CONFIG = _get_all_system_config()
    except Exception as e:
        print("请先进行数据库迁移!")  # 提示用户先运行数据库迁移命令
    return


def refresh_dictionary():
    """
    刷新字典配置
    
    重新从数据库加载字典配置并更新到缓存或内存
    通常在字典数据发生变更时调用
    """
    # 如果使用Redis缓存模式
    if dispatch_db_type == 'redis':
        cache.set(f"init_dictionary", _get_all_dictionary())
        return
        
    # 如果启用多租户模式
    if is_tenants_mode():
        from django_tenants.utils import tenant_context, get_tenant_model

        # 为每个租户刷新字典配置
        for tenant in get_tenant_model().objects.filter():
            with tenant_context(tenant):  # 切换到指定租户的数据库schema
                settings.DICTIONARY_CONFIG[connection.tenant.schema_name] = _get_all_dictionary()
    else:
        # 单租户模式，直接更新settings
        settings.DICTIONARY_CONFIG = _get_all_dictionary()


def refresh_system_config():
    """
    刷新系统配置
    
    重新从数据库加载系统配置并更新到缓存或内存
    通常在系统配置发生变更时调用
    """
    # 如果使用Redis缓存模式
    if dispatch_db_type == 'redis':
        cache.set(f"init_system_config", _get_all_system_config())
        return
        
    # 如果启用多租户模式
    if is_tenants_mode():
        from django_tenants.utils import tenant_context, get_tenant_model

        # 为每个租户刷新系统配置
        for tenant in get_tenant_model().objects.filter():
            with tenant_context(tenant):  # 切换到指定租户的数据库schema
                settings.SYSTEM_CONFIG[connection.tenant.schema_name] = _get_all_system_config()
    else:
        # 单租户模式，直接更新settings
        settings.SYSTEM_CONFIG = _get_all_system_config()


# ================================================= #
# ******************** 字典管理模块 ******************** #
# ================================================= #

def get_dictionary_config(schema_name=None):
    """
    获取字典所有配置
    
    Args:
        schema_name (str, optional): 租户schema名称，多租户模式下使用
                                   如果不提供，使用当前连接的租户schema
    
    Returns:
        dict: 完整的字典配置字典，如果配置不存在则返回空字典
    """
    # 如果使用Redis缓存模式
    if dispatch_db_type == 'redis':
        init_dictionary_data = cache.get(f"init_dictionary")  # 尝试从缓存获取
        if not init_dictionary_data:  # 如果缓存中没有数据
            refresh_dictionary()  # 刷新字典配置到缓存
        return cache.get(f"init_dictionary") or {}  # 返回缓存数据或空字典
    
    # 如果settings中没有字典配置，先刷新一次
    if not settings.DICTIONARY_CONFIG:
        refresh_dictionary()
        
    # 多租户模式下，根据schema_name获取对应租户的配置
    if is_tenants_mode():
        dictionary_config = settings.DICTIONARY_CONFIG[schema_name or connection.tenant.schema_name]
    else:
        # 单租户模式，直接从settings获取
        dictionary_config = settings.DICTIONARY_CONFIG
        
    return dictionary_config or {}  # 返回字典配置或空字典


def get_dictionary_values(key, schema_name=None):
    """
    获取指定key的字典数据数组
    
    Args:
        key (str): 字典编号（字典的value值）
        schema_name (str, optional): 租户schema名称
    
    Returns:
        dict: 包含id、value、children的字典项，如果找不到则返回None
    """
    # 如果使用Redis缓存模式
    if dispatch_db_type == 'redis':
        dictionary_config = cache.get(f"init_dictionary")  # 从缓存获取字典配置
        if not dictionary_config:  # 如果缓存中没有数据
            refresh_dictionary()  # 刷新字典配置
            dictionary_config = cache.get(f"init_dictionary")  # 重新获取
        return dictionary_config.get(key)  # 返回指定key的字典项
    
    # 获取完整的字典配置
    dictionary_config = get_dictionary_config(schema_name)
    return dictionary_config.get(key)  # 返回指定key的字典项


def get_dictionary_label(key, name, schema_name=None):
    """
    获取字典项的标签(label)值
    
    根据字典key和值name，查找对应的显示标签
    
    Args:
        key (str): 字典管理中的key值（字典编号）
        name (str): 对应字典配置的value值
        schema_name (str, optional): 租户schema名称
    
    Returns:
        str: 对应的标签值，如果找不到则返回空字符串
    """
    # 获取指定key的字典数据
    res = get_dictionary_values(key, schema_name) or []
    
    # 遍历字典的子项列表
    for ele in res.get('children'):
        # 如果找到匹配的value值（转为字符串比较）
        if ele.get("value") == str(name):
            return ele.get("label")  # 返回对应的标签
    
    return ""  # 如果没找到，返回空字符串


# ================================================= #
# ******************** 系统配置模块 ******************** #
# ================================================= #

def get_system_config(schema_name=None):
    """
    获取系统配置中所有配置
    
    返回格式: { "父级key.子级key" : "值" }
    
    Args:
        schema_name (str, optional): 租户schema名称，多租户模式下使用
    
    Returns:
        dict: 完整的系统配置字典，键名格式为"父级key.子级key"
    """
    # 如果使用Redis缓存模式
    if dispatch_db_type == 'redis':
        init_dictionary_data = cache.get(f"init_system_config")  # 从缓存获取系统配置
        if not init_dictionary_data:  # 如果缓存中没有数据
            refresh_system_config()  # 刷新系统配置到缓存
        return cache.get(f"init_system_config") or {}  # 返回缓存数据或空字典
    
    # 如果settings中没有系统配置，先刷新一次
    if not settings.SYSTEM_CONFIG:
        refresh_system_config()
        
    # 多租户模式下，根据schema_name获取对应租户的配置
    if is_tenants_mode():
        dictionary_config = settings.SYSTEM_CONFIG[schema_name or connection.tenant.schema_name]
    else:
        # 单租户模式，直接从settings获取
        dictionary_config = settings.SYSTEM_CONFIG
        
    return dictionary_config or {}  # 返回系统配置或空字典


def get_system_config_values(key, schema_name=None):
    """
    获取指定key的系统配置数据
    
    Args:
        key (str): 系统配置的key值，格式为"父级key.子级key"
        schema_name (str, optional): 租户schema名称
    
    Returns:
        any: 系统配置的值，类型根据配置而定（可能是字符串、数组等）
    """
    # 如果使用Redis缓存模式
    if dispatch_db_type == 'redis':
        system_config = cache.get(f"init_system_config")  # 从缓存获取系统配置
        if not system_config:  # 如果缓存中没有数据
            refresh_system_config()  # 刷新系统配置
            system_config = cache.get(f"init_system_config")  # 重新获取
        return system_config.get(key)  # 返回指定key的配置值
    
    # 获取完整的系统配置
    system_config = get_system_config(schema_name)
    return system_config.get(key)  # 返回指定key的配置值


def get_system_config_values_to_dict(key, schema_name=None):
    """
    获取系统配置数据并转换为字典
    
    **仅限于数组类型的系统配置**
    将数组中每个元素的key作为字典键，value作为字典值
    
    Args:
        key (str): 系统配置的key值
        schema_name (str, optional): 租户schema名称
    
    Returns:
        dict: 转换后的字典，格式为 {元素key: 元素value}
    
    Raises:
        CustomValidationError: 如果配置不是数组类型
    """
    values_dict = {}  # 初始化结果字典
    config_values = get_system_config_values(key, schema_name)  # 获取配置值
    
    # 检查配置值是否为列表类型
    if not isinstance(config_values, list):
        raise CustomValidationError("该方式仅限于数组类型系统配置")
    
    # 遍历配置数组，构建字典
    for ele in get_system_config_values(key, schema_name):
        values_dict[ele.get('key')] = ele.get('value')
        
    return values_dict


def get_system_config_label(key, name, schema_name=None):
    """
    获取系统配置项的标签(label)值
    
    根据系统配置key和值name，查找对应的显示标签
    
    Args:
        key (str): 系统配置中的key值
        name (str): 对应系统配置的value值  
        schema_name (str, optional): 租户schema名称
    
    Returns:
        str: 对应的标签值，如果找不到则返回空字符串
    """
    # 获取指定key的系统配置数据（应该是数组类型）
    children = get_system_config_values(key, schema_name) or []
    
    # 遍历配置数组
    for ele in children:
        # 如果找到匹配的value值（转为字符串比较）
        if ele.get("value") == str(name):
            return ele.get("label")  # 返回对应的标签
    
    return ""  # 如果没找到，返回空字符串
