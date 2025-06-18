# 导入functools模块，用于创建装饰器和函数工具
import functools
# 导入os模块，用于操作系统相关功能，如环境变量设置
import os

# 从celery信号模块导入任务后处理信号，用于任务完成后的回调处理
from celery.signals import task_postrun

# 设置Django配置模块的环境变量，指向项目设置文件
# 如果环境变量DJANGO_SETTINGS_MODULE不存在，则设置为'application.settings'
# 这告诉Django在哪里找到项目的配置文件
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings')

# 从Django配置模块导入settings对象，用于访问项目配置
from django.conf import settings
# 从celery导入platforms模块，用于平台相关的配置
from celery import platforms

# Django INSTALLED_APPS 应用配置和多租户支持检查
# 
# INSTALLED_APPS是Django项目的核心配置项，类似于Spring Boot的自动配置机制：
# 1. 应用注册：列出项目中启用的所有Django应用（apps）
# 2. 功能模块化：每个应用提供特定功能，如用户认证、管理界面、REST API等
# 3. 自动发现：Django会自动发现并加载这些应用中的模型、视图、URL配置等
# 4. 扩展机制：通过添加第三方应用来扩展项目功能
# 
# 常见的INSTALLED_APPS应用示例：
# - 'django.contrib.admin'：Django管理后台
# - 'django.contrib.auth'：用户认证系统
# - 'django.contrib.contenttypes'：内容类型框架
# - 'rest_framework'：Django REST框架
# - 'channels'：WebSocket支持
# - 'django_tenants'：多租户支持
# - 自定义应用如：'users', 'products', 'orders'等

# 检查Django项目是否安装了django_tenants应用（多租户支持）
# django_tenants是一个第三方应用，为Django提供多租户架构支持
# 多租户允许单个应用实例服务多个客户（租户），每个租户的数据相互隔离
if "django_tenants" in settings.INSTALLED_APPS:
    # 如果使用了多租户，导入租户感知的Celery应用类
    # TenantAwareCeleryApp能够处理多租户环境下的任务分发
    # 确保Celery任务在正确的租户上下文中执行
    from tenant_schemas_celery.app import CeleryApp as TenantAwareCeleryApp

    # 创建支持多租户的Celery应用实例
    # 这个实例会自动处理租户上下文的切换和任务路由
    app = TenantAwareCeleryApp()
else:
    # 如果不使用多租户，导入标准的Celery类
    # 标准Celery应用适用于单租户或不需要租户隔离的场景
    from celery import Celery

    # 创建标准的Celery应用实例，应用名称为"application"
    # 这个名称用于标识Celery应用，在监控和日志中会显示
    # 创建标准的Celery应用实例，应用名称为"application"
    # 这个名称用于标识Celery应用，在监控和日志中会显示
    
    # f"application" 中的 'f' 表示这是一个 f-string（格式化字符串字面值）
    # f-string 是 Python 3.6+ 引入的字符串格式化语法，允许在字符串中嵌入表达式
    # 语法格式：f"文本{变量或表达式}文本"
    # 在这个例子中，由于字符串内没有 {} 占位符，所以 f"application" 等同于 "application"
    # 但使用 f-string 为后续可能需要动态生成应用名称预留了扩展性
    # 例如：f"application-{environment}" 或 f"application-{tenant_id}" 等
    app = Celery(f"application")

# 从Django配置中加载Celery配置
# 
# Celery概念理解：
# Celery是Python生态系统中的分布式任务队列系统，用于处理异步任务和定时任务
# 
# Java生态中的对应技术：
# 1. Spring Boot + RabbitMQ/Redis + @Async注解 - 类似于Celery的异步任务处理
# 2. Quartz Scheduler - 对应Celery的定时任务功能（类似于Celery Beat）
# 3. Spring Integration + Message Queue - 对应Celery的消息传递机制
# 4. Apache Kafka + Spring Cloud Stream - 处理大规模分布式任务
# 5. Spring Batch - 用于批处理任务，类似Celery的批量任务处理
# 
# Celery架构组件及Java对应：
# - Celery Worker（工作进程） ≈ Spring Boot应用实例 + @RabbitListener
# - Celery Beat（定时调度器） ≈ Quartz Scheduler + @Scheduled
# - Broker（消息代理） ≈ RabbitMQ/Apache ActiveMQ/Redis
# - Backend（结果存储） ≈ Redis/数据库存储执行结果
# 
# 使用场景对比：
# Python Celery: 发送邮件、图像处理、数据分析、定时报表生成
# Java Spring: @Async邮件发送、@Scheduled定时任务、消息队列处理
# 
# namespace='CELERY'表示只加载以CELERY_开头的配置项
# 例如：CELERY_BROKER_URL, CELERY_RESULT_BACKEND等
# 类似于Spring Boot中的@ConfigurationProperties(prefix="celery")
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务模块
# 在settings.INSTALLED_APPS中列出的每个应用中查找tasks.py文件
# 并自动注册其中定义的Celery任务
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# 允许以root用户身份运行Celery
# 在生产环境中通常不建议这样做，但在开发或容器环境中可能需要
platforms.C_FORCE_ROOT = True


def retry_base_task_error():
    """
    Celery任务失败重试装饰器工厂函数
    
    这是一个装饰器工厂模式的实现，包含三层嵌套结构：
    
    第一层：retry_base_task_error() - 装饰器工厂函数
    ├── 作用：返回一个可重用的装饰器
    ├── 好处：可以预设重试参数（3次重试，180秒间隔）
    └── 使用方式：@retry_base_task_error()  # 注意有括号
    
    第二层：wraps(func) - 真正的装饰器函数
    ├── 作用：接收要被装饰的函数作为参数
    ├── 返回：包装后的函数（wrapper）
    └── 职责：配置Celery任务参数和异常处理逻辑
    
    第三层：wrapper(self, *args, **kwargs) - 最终执行的包装函数
    ├── 作用：替代原始函数被调用
    ├── 包含：异常捕获和重试逻辑
    └── 执行：调用原始函数并处理可能的异常
    
    嵌套结构的执行流程：
    1. 调用 retry_base_task_error() 返回 wraps 函数
    2. 使用 @wraps 装饰目标函数，返回 wrapper 函数
    3. 实际调用时执行 wrapper 函数，内部调用原始函数
    
    :return: 装饰器函数
    """

    def wraps(func):
        """
        内部装饰器函数 - 负责包装目标函数
        
        wraps函数的作用详解：
        
        1. 接收参数：
           - func: 需要被装饰的原始函数（如发送邮件、处理数据等业务函数）
        
        2. 添加Celery功能：
           - @app.task: 将普通函数转换为Celery异步任务
           - bind=True: 让函数可以访问任务实例(self)，用于重试控制
           - retry_delay=180: 设置重试间隔时间
           - max_retries=3: 设置最大重试次数
        
        3. 保持函数特性：
           - @functools.wraps(func): 保持原函数的__name__、__doc__等元数据
           - 确保装饰后的函数在调试时仍显示原始函数信息
        
        4. 异常处理：
           - 在wrapper中捕获所有异常
           - 自动触发Celery重试机制
           - 避免任务因异常而直接失败
        
        实际使用示例：
        @retry_base_task_error()  # 调用工厂函数，返回wraps装饰器
        def send_email_task(to_email, subject, content):
            # 发送邮件的业务逻辑
            pass
        
        等价于：
        def send_email_task(to_email, subject, content):
            # 发送邮件的业务逻辑
            pass
        send_email_task = retry_base_task_error()(send_email_task)
        """
        # 使用app.task装饰器创建Celery任务
        # bind=True: 将任务实例作为第一个参数传递给函数
        # retry_delay=180: 重试延迟时间为180秒（3分钟）
        # max_retries=3: 最大重试次数为3次
        @app.task(bind=True, retry_delay=180, max_retries=3)
        # 使用functools.wraps保持原函数的元数据（如函数名、文档字符串等）
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            """
            最终的包装函数 - 实际被调用的函数
            
            参数说明：
            - self: Celery任务实例，由于bind=True而传入
            - *args: 原始函数的位置参数
            - **kwargs: 原始函数的关键字参数
            
            执行逻辑：
            1. 尝试执行原始业务函数
            2. 如果成功，直接返回结果
            3. 如果失败，触发Celery重试机制
            """
            try:
                # 尝试执行原始函数
                return func(*args, **kwargs)
            except Exception as exc:
                # 如果发生异常，触发任务重试
                # exc=exc 将异常信息传递给重试机制
                raise self.retry(exc=exc)

        # 返回包装后的函数
        return wrapper

    # 返回装饰器函数
    return wraps


# Celery信号处理机制 - 任务后处理信号连接
# 
# 这个函数的作用：
# 1. 监听所有Celery任务的完成事件（成功或失败都会触发）
# 2. 为周期性任务（periodic tasks）在数据库中添加标识信息
# 3. 增强django-celery-results的功能，便于区分普通任务和周期性任务
#
# 为什么定义在这个文件中：
# - celery.py是Celery应用的配置文件，负责初始化和配置Celery
# - 信号处理器需要在Celery启动时就注册，放在这里确保及时生效
# - 这是Celery应用级别的全局信号处理，属于基础设施配置
#
# 是否自动生成：
# - 不是自动生成的，这是开发者手动编写的自定义信号处理器
# - 主要用于解决django-celery-beat和django-celery-results集成时的功能增强
# - 原生的django-celery-results不会自动标识周期性任务，需要自定义实现
@task_postrun.connect
def add_periodic_task_name(sender, task_id, task, args, kwargs, **extras):
    """
    任务后处理信号处理函数 - 自定义的周期性任务标识增强功能
    
    技术背景：
    - Celery的信号机制类似于Django的signals，采用观察者模式
    - task_postrun信号在每个任务执行完成后触发，无论成功失败
    - 通过信号处理可以实现任务执行的统计、日志、清理等横切关注点
    
    业务背景：
    - django-celery-beat负责调度周期性任务
    - django-celery-results负责存储任务执行结果
    - 两者默认情况下没有关联，无法直接识别哪些结果来自周期性任务
    - 这个函数弥补了这个功能缺失，为任务结果添加周期性任务标识
    
    :param sender: 发送信号的任务类，即执行完成的任务
    :param task_id: 唯一的任务执行ID，用于在结果表中定位记录
    :param task: 任务实例对象，包含任务的详细信息
    :param args: 任务执行时的位置参数
    :param kwargs: 任务执行时的关键字参数，周期性任务的名称就在这里
    :param extras: 信号系统传递的额外参数
    """
    # 从任务的关键字参数中提取周期性任务名称
    # django-celery-beat在调度周期性任务时会自动添加这个参数
    periodic_task_name = kwargs.get('periodic_task_name')
    
    # 只有当任务确实是周期性任务时才进行处理
    if periodic_task_name:
        # 导入TaskResult模型 - django-celery-results的核心数据模型
        # 该模型存储任务的执行结果、状态、时间戳等信息
        from django_celery_results.models import TaskResult
        
        # 更新任务结果记录，添加周期性任务标识
        # 这样在查询任务结果时就能区分普通任务和周期性任务
        # 对于监控、统计、报表等功能非常有用
        TaskResult.objects.filter(task_id=task_id).update(periodic_task_name=periodic_task_name)
