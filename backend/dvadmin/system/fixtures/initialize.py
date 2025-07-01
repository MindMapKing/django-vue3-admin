"""
系统初始化脚本
==============

该文件是Django-Vue3-Admin项目的系统初始化脚本，主要功能包括：

1. **基础数据初始化**：初始化系统运行所需的基础数据
2. **权限体系构建**：建立完整的RBAC权限管理体系
3. **演示数据创建**：为演示和测试提供标准数据集
4. **系统配置设置**：初始化系统默认配置参数

初始化顺序：
1. 部门组织架构 → 2. 角色定义 → 3. 用户账户 → 4. 菜单权限 
→ 5. 角色菜单关联 → 6. 角色按钮权限 → 7. API白名单 
→ 8. 数据字典 → 9. 系统配置

使用方式：
- 直接执行：python initialize.py
- 程序调用：Initialize(app='dvadmin.system').run()
"""

# 初始化Django环境配置
import os
import django

# 设置Django配置模块环境变量
# 这确保脚本能够独立运行，无需通过manage.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "application.settings")

# 初始化Django应用
# 必须在导入Django模型之前调用，否则会出现AppRegistryNotReady错误
django.setup()

# 导入核心初始化基类
from dvadmin.utils.core_initialize import CoreInitialize

# 导入所有数据初始化序列化器
# 这些序列化器定义了各种数据模型的初始化逻辑和验证规则
from dvadmin.system.fixtures.initSerializer import (
    UsersInitSerializer,              # 用户初始化序列化器
    DeptInitSerializer,               # 部门初始化序列化器  
    RoleInitSerializer,               # 角色初始化序列化器
    MenuInitSerializer,               # 菜单初始化序列化器
    ApiWhiteListInitSerializer,       # API白名单初始化序列化器
    DictionaryInitSerializer,         # 数据字典初始化序列化器
    SystemConfigInitSerializer,       # 系统配置初始化序列化器
    RoleMenuInitSerializer,           # 角色菜单关联初始化序列化器
    RoleMenuButtonInitSerializer      # 角色菜单按钮权限初始化序列化器
)


class Initialize(CoreInitialize):
    """
    系统初始化主类
    
    继承自CoreInitialize基类，实现了Django-Vue3-Admin项目的
    完整系统初始化流程。每个初始化方法对应一个数据模块，
    按照依赖关系的顺序执行初始化。
    
    设计特点：
    - 幂等性：多次执行不会产生重复数据
    - 依赖处理：自动处理模块间的依赖关系
    - 错误恢复：单个模块失败不影响其他模块
    - 日志记录：详细记录初始化过程和结果
    """

    def init_dept(self):
        """
        初始化部门组织架构
        
        部门是用户管理和权限分配的基础，必须最先初始化。
        支持多级部门层级结构，每个部门可以有唯一的key标识。
        
        初始化内容：
        - 根部门（如：DVAdmin团队）
        - 子部门（如：技术部、运营部）
        - 部门层级关系
        
        唯一性校验字段：
        - name: 部门名称（同级别下唯一）
        - parent: 父部门ID
        - key: 部门标识符（全局唯一）
        """
        self.init_base(DeptInitSerializer, unique_fields=['name', 'parent','key'])

    def init_role(self):
        """
        初始化角色权限体系
        
        角色是RBAC权限模型的核心，定义了不同的权限级别。
        每个角色通过key字段进行唯一标识，便于权限关联。
        
        初始化内容：
        - 超级管理员角色（admin）
        - 普通管理员角色
        - 普通用户角色（public）
        - 其他业务角色
        
        唯一性校验字段：
        - key: 角色标识符（全局唯一，用于权限关联）
        """
        self.init_base(RoleInitSerializer, unique_fields=['key'])

    def init_users(self):
        """
        初始化系统用户账户
        
        创建系统默认用户，包括管理员和测试用户。
        用户会自动关联到相应的部门和角色。
        
        初始化内容：
        - 超级管理员账户（superadmin）
        - 普通管理员账户（admin）  
        - 测试用户账户（test）
        
        关联处理：
        - 通过role_key关联到角色
        - 通过dept_key关联到部门
        
        唯一性校验字段：
        - username: 用户名（全局唯一）
        """
        self.init_base(UsersInitSerializer, unique_fields=['username'])

    def init_menu(self):
        """
        初始化菜单权限体系
        
        菜单是前端页面访问控制的基础，定义了系统的功能模块
        和页面访问权限。支持多级菜单结构和动态路由。
        
        初始化内容：
        - 系统管理菜单
        - 用户管理功能
        - 权限管理功能
        - 各种业务功能菜单
        
        菜单特性：
        - 支持目录菜单和页面菜单
        - 关联前端路由和组件
        - 控制菜单显示和缓存
        
        唯一性校验字段：
        - name: 菜单名称
        - web_path: 前端路由路径
        - component: 前端组件路径
        - component_name: 前端组件名称
        """
        self.init_base(MenuInitSerializer, unique_fields=['name', 'web_path', 'component', 'component_name'])

    def init_role_menu(self):
        """
        初始化角色菜单权限关联
        
        建立角色与菜单之间的访问权限关联关系。
        定义了哪些角色可以访问哪些菜单页面。
        
        权限控制：
        - 角色级别的菜单访问控制
        - 支持细粒度的页面权限管理
        - 动态菜单显示控制
        
        关联逻辑：
        - 通过role__key关联角色
        - 通过menu__web_path和menu__component_name关联菜单
        
        唯一性校验字段：
        - role__key: 角色标识
        - menu__web_path: 菜单路由路径
        - menu__component_name: 菜单组件名称
        """
        self.init_base(RoleMenuInitSerializer, unique_fields=['role__key', 'menu__web_path', 'menu__component_name'])

    def init_role_menu_button(self):
        """
        初始化角色菜单按钮权限关联
        
        建立角色与菜单按钮之间的操作权限关联关系。
        控制用户在特定页面上可以执行的具体操作。
        
        按钮权限类型：
        - 增加(add)、删除(delete)、修改(edit)、查看(view)
        - 导入(import)、导出(export)
        - 审核(audit)、发布(publish)等业务操作
        
        权限粒度：
        - 页面级别的操作控制
        - 按钮显示隐藏控制
        - API接口访问控制
        
        唯一性校验字段：
        - role__key: 角色标识
        - menu_button__value: 按钮权限值
        """
        self.init_base(RoleMenuButtonInitSerializer, unique_fields=['role__key', 'menu_button__value'])

    def init_api_white_list(self):
        """
        初始化API接口白名单
        
        定义无需权限验证即可访问的API接口列表。
        主要用于公共接口和登录相关的接口。
        
        白名单接口类型：
        - 用户登录、注册接口
        - 公共数据查询接口
        - 系统状态检查接口
        - 文件上传下载接口（部分）
        
        配置内容：
        - URL路径匹配规则
        - HTTP请求方法（GET、POST等）
        - 是否启用数据源控制
        
        唯一性校验字段：
        - url: API接口路径
        - method: HTTP请求方法
        """
        self.init_base(ApiWhiteListInitSerializer, unique_fields=['url', 'method', ])

    def init_dictionary(self):
        """
        初始化系统数据字典
        
        数据字典是系统中下拉选择、状态值等枚举数据的
        统一管理机制，支持层级结构和动态配置。
        
        字典数据类型：
        - 用户性别（男、女）
        - 用户状态（启用、禁用）
        - 数据范围（全部、本部门、本人）
        - 消息类型（通知、公告、私信）
        - 其他业务枚举值
        
        字典特性：
        - 支持父子层级结构
        - 颜色标签支持
        - 状态控制（启用/禁用）
        - 排序支持
        
        唯一性校验字段：
        - value: 字典值
        - parent: 父字典ID
        """
        self.init_base(DictionaryInitSerializer, unique_fields=['value', 'parent', ])

    def init_system_config(self):
        """
        初始化系统配置参数
        
        系统配置是项目运行时可动态调整的参数设置，
        包括系统基础配置、业务规则配置等。
        
        配置参数类型：
        - 系统基础信息（网站名称、Logo等）
        - 安全设置（密码策略、登录限制等）
        - 文件上传配置（大小限制、格式限制等）
        - 邮件短信配置（SMTP、短信接口等）
        - 业务规则配置（审批流程、数据保留期等）
        
        配置特性：
        - 支持多种表单控件类型
        - 数据验证规则支持
        - 层级分组管理
        - 热更新支持
        
        唯一性校验字段：
        - key: 配置项标识
        - parent: 父配置分组ID
        """
        self.init_base(SystemConfigInitSerializer, unique_fields=['key', 'parent', ])

    def run(self):
        """
        执行完整的系统初始化流程
        
        按照数据依赖关系的正确顺序执行所有初始化步骤。
        这个顺序非常重要，因为后面的数据依赖前面的数据。
        
        初始化顺序解释：
        1. init_dept()         - 部门：用户需要关联部门
        2. init_role()         - 角色：用户需要关联角色
        3. init_users()        - 用户：权限关联需要用户存在
        4. init_menu()         - 菜单：权限关联需要菜单存在
        5. init_role_menu()    - 角色菜单权限：建立访问控制
        6. init_role_menu_button() - 角色按钮权限：建立操作控制
        7. init_api_white_list()   - API白名单：配置免权限接口
        8. init_dictionary()       - 数据字典：系统枚举数据
        9. init_system_config()    - 系统配置：运行时参数
        
        执行特点：
        - 事务性：单个步骤失败不影响其他步骤
        - 日志记录：详细记录每个步骤的执行情况
        - 进度提示：显示初始化进度和结果
        """
        # 按依赖顺序执行初始化
        self.init_dept()                # 1. 初始化部门组织架构
        self.init_role()                # 2. 初始化角色权限体系
        self.init_users()               # 3. 初始化系统用户账户
        self.init_menu()                # 4. 初始化菜单权限体系
        self.init_role_menu()           # 5. 初始化角色菜单权限关联
        self.init_role_menu_button()    # 6. 初始化角色菜单按钮权限关联
        self.init_api_white_list()      # 7. 初始化API接口白名单
        self.init_dictionary()          # 8. 初始化系统数据字典
        self.init_system_config()       # 9. 初始化系统配置参数


# 脚本入口点
if __name__ == "__main__":
    """
    脚本直接执行入口
    
    当直接运行此脚本时（python initialize.py），
    会创建Initialize实例并执行完整的初始化流程。
    
    参数说明：
    - app='dvadmin.system': 指定要初始化的Django应用
    
    执行效果：
    - 在数据库中创建所有必需的基础数据
    - 建立完整的权限管理体系
    - 创建可用的管理员账户
    - 配置系统默认参数
    
    注意事项：
    - 确保数据库已迁移（python manage.py migrate）
    - 确保数据库连接正常
    - 多次执行是安全的（幂等性）
    """
    Initialize(app='dvadmin.system').run()
