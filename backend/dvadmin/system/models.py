import hashlib
import os
from time import time
from pathlib import PurePosixPath

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from application import dispatch
from dvadmin.utils.models import CoreModel, table_prefix, get_custom_app_models

from dvadmin3_flow.base_model import FlowBaseModel
class Role(CoreModel,FlowBaseModel):
    name = models.CharField(max_length=64, verbose_name="角色名称", help_text="角色名称")
    key = models.CharField(max_length=64, unique=True, verbose_name="权限字符", help_text="权限字符")
    sort = models.IntegerField(default=1, verbose_name="角色顺序", help_text="角色顺序")
    status = models.BooleanField(default=True, verbose_name="角色状态", help_text="角色状态")

    class Meta:
        db_table = table_prefix + "system_role"
        verbose_name = "角色表"
        verbose_name_plural = verbose_name
        ordering = ("sort",)


class CustomUserManager(UserManager):

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        user = super(CustomUserManager, self).create_superuser(username, email, password, **extra_fields)
        user.set_password(password)
        try:
            user.role.add(Role.objects.get(name="管理员"))
            user.save(using=self._db)
            return user
        except ObjectDoesNotExist:
            user.delete()
            raise ValidationError("角色`管理员`不存在, 创建失败, 请先执行python manage.py init")


class Users(CoreModel, AbstractUser):
    username = models.CharField(max_length=150, unique=True, db_index=True, verbose_name="用户账号",
                                help_text="用户账号")
    email = models.EmailField(max_length=255, verbose_name="邮箱", null=True, blank=True, help_text="邮箱")
    mobile = models.CharField(max_length=255, verbose_name="电话", null=True, blank=True, help_text="电话")
    avatar = models.CharField(max_length=255, verbose_name="头像", null=True, blank=True, help_text="头像")
    name = models.CharField(max_length=40, verbose_name="姓名", help_text="姓名")
    GENDER_CHOICES = (
        (0, "未知"),
        (1, "男"),
        (2, "女"),
    )
    gender = models.IntegerField(
        choices=GENDER_CHOICES, default=0, verbose_name="性别", null=True, blank=True, help_text="性别"
    )
    USER_TYPE = (
        (0, "后台用户"),
        (1, "前台用户"),
    )
    user_type = models.IntegerField(
        choices=USER_TYPE, default=0, verbose_name="用户类型", null=True, blank=True, help_text="用户类型"
    )
    post = models.ManyToManyField(to="Post", blank=True, verbose_name="关联岗位", db_constraint=False,
                                  help_text="关联岗位")
    role = models.ManyToManyField(to="Role", blank=True, verbose_name="关联角色", db_constraint=False,
                                  help_text="关联角色")
    dept = models.ForeignKey(
        to="Dept",
        verbose_name="所属部门",
        on_delete=models.PROTECT,
        db_constraint=False,
        null=True,
        blank=True,
        help_text="关联部门",
    )
    login_error_count = models.IntegerField(default=0, verbose_name="登录错误次数", help_text="登录错误次数")
    pwd_change_count = models.IntegerField(default=0,blank=True, verbose_name="密码修改次数", help_text="密码修改次数")
    objects = CustomUserManager()

    def set_password(self, raw_password):
        super().set_password(hashlib.md5(raw_password.encode(encoding="UTF-8")).hexdigest())

    class Meta:
        db_table = table_prefix + "system_users"
        verbose_name = "用户表"
        verbose_name_plural = verbose_name
        ordering = ("-create_datetime",)


class Post(CoreModel):
    name = models.CharField(null=False, max_length=64, verbose_name="岗位名称", help_text="岗位名称")
    code = models.CharField(max_length=32, verbose_name="岗位编码", help_text="岗位编码")
    sort = models.IntegerField(default=1, verbose_name="岗位顺序", help_text="岗位顺序")
    STATUS_CHOICES = (
        (0, "离职"),
        (1, "在职"),
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name="岗位状态", help_text="岗位状态")

    class Meta:
        db_table = table_prefix + "system_post"
        verbose_name = "岗位表"
        verbose_name_plural = verbose_name
        ordering = ("sort",)


class Dept(CoreModel):
    name = models.CharField(max_length=64, verbose_name="部门名称", help_text="部门名称")
    key = models.CharField(max_length=64, unique=True, null=True, blank=True, verbose_name="关联字符", help_text="关联字符")
    sort = models.IntegerField(default=1, verbose_name="显示排序", help_text="显示排序")
    owner = models.CharField(max_length=32, verbose_name="负责人", null=True, blank=True, help_text="负责人")
    phone = models.CharField(max_length=32, verbose_name="联系电话", null=True, blank=True, help_text="联系电话")
    email = models.EmailField(max_length=32, verbose_name="邮箱", null=True, blank=True, help_text="邮箱")
    status = models.BooleanField(default=True, verbose_name="部门状态", null=True, blank=True, help_text="部门状态")
    parent = models.ForeignKey(
        to="Dept",
        on_delete=models.CASCADE,
        default=None,
        verbose_name="上级部门",
        db_constraint=False,
        null=True,
        blank=True,
        help_text="上级部门",
    )

    @classmethod
    def _recursion(cls, instance, parent, result):
        new_instance = getattr(instance, parent, None)
        res = []
        data = getattr(instance, result, None)
        if data:
            res.append(data)
        if new_instance:
            array = cls._recursion(new_instance, parent, result)
            res += array
        return res

    @classmethod
    def get_region_name(cls, obj):
        """
        获取某个用户的递归所有部门名称
        """
        dept_name_all = cls._recursion(obj, "parent", "name")
        dept_name_all.reverse()
        return "/".join(dept_name_all)

    @classmethod
    def recursion_all_dept(cls, dept_id: int, dept_all_list=None, dept_list=None):
        """
        递归获取部门的所有下级部门
        :param dept_id: 需要获取的id
        :param dept_all_list: 所有列表
        :param dept_list: 递归list
        :return:
        """
        if not dept_all_list:
            dept_all_list = Dept.objects.values("id", "parent")
        if dept_list is None:
            dept_list = [dept_id]
        for ele in dept_all_list:
            if ele.get("parent") == dept_id:
                dept_list.append(ele.get("id"))
                cls.recursion_all_dept(ele.get("id"), dept_all_list, dept_list)
        return list(set(dept_list))

    class Meta:
        db_table = table_prefix + "system_dept"
        verbose_name = "部门表"
        verbose_name_plural = verbose_name
        ordering = ("sort",)


class Menu(CoreModel):
    parent = models.ForeignKey(
        to="Menu",
        on_delete=models.CASCADE,
        verbose_name="上级菜单",
        null=True,
        blank=True,
        db_constraint=False,
        help_text="上级菜单",
    )
    icon = models.CharField(max_length=64, verbose_name="菜单图标", null=True, blank=True, help_text="菜单图标")
    name = models.CharField(max_length=64, verbose_name="菜单名称", help_text="菜单名称")
    sort = models.IntegerField(default=1, verbose_name="显示排序", null=True, blank=True, help_text="显示排序")
    ISLINK_CHOICES = (
        (0, "否"),
        (1, "是"),
    )
    is_link = models.BooleanField(default=False, verbose_name="是否外链", help_text="是否外链")
    link_url = models.CharField(max_length=255, verbose_name="链接地址", null=True, blank=True, help_text="链接地址")
    is_catalog = models.BooleanField(default=False, verbose_name="是否目录", help_text="是否目录")
    web_path = models.CharField(max_length=128, verbose_name="路由地址", null=True, blank=True, help_text="路由地址")
    component = models.CharField(max_length=128, verbose_name="组件地址", null=True, blank=True, help_text="组件地址")
    component_name = models.CharField(max_length=50, verbose_name="组件名称", null=True, blank=True,
                                      help_text="组件名称")
    status = models.BooleanField(default=True, blank=True, verbose_name="菜单状态", help_text="菜单状态")
    cache = models.BooleanField(default=False, blank=True, verbose_name="是否页面缓存", help_text="是否页面缓存")
    visible = models.BooleanField(default=True, blank=True, verbose_name="侧边栏中是否显示",
                                  help_text="侧边栏中是否显示")
    is_iframe = models.BooleanField(default=False, blank=True, verbose_name="框架外显示", help_text="框架外显示")
    is_affix = models.BooleanField(default=False, blank=True, verbose_name="是否固定", help_text="是否固定")

    @classmethod
    def get_all_parent(cls, id: int, all_list=None, nodes=None):
        """
        递归获取给定ID的所有层级
        :param id: 参数ID
        :param all_list: 所有列表
        :param nodes: 递归列表
        :return: nodes
        """
        if not all_list:
            all_list = Menu.objects.values("id", "name", "parent")
        if nodes is None:
            nodes = []
        for ele in all_list:
            if ele.get("id") == id:
                parent_id = ele.get("parent")
                if parent_id is not None:
                    cls.get_all_parent(parent_id, all_list, nodes)
                nodes.append(ele)
        return nodes
    class Meta:
        db_table = table_prefix + "system_menu"
        verbose_name = "菜单表"
        verbose_name_plural = verbose_name
        ordering = ("sort",)

class MenuField(CoreModel):
    model = models.CharField(max_length=64, verbose_name='表名')
    menu = models.ForeignKey(to='Menu', on_delete=models.CASCADE, verbose_name='菜单', db_constraint=False)
    field_name = models.CharField(max_length=64, verbose_name='模型表字段名')
    title = models.CharField(max_length=64, verbose_name='字段显示名')
    class Meta:
        db_table = table_prefix + "system_menu_field"
        verbose_name = "菜单字段表"
        verbose_name_plural = verbose_name
        ordering = ("id",)

class FieldPermission(CoreModel):
    role = models.ForeignKey(to='Role', on_delete=models.CASCADE, verbose_name='角色', db_constraint=False)
    field = models.ForeignKey(to='MenuField', on_delete=models.CASCADE,related_name='menu_field', verbose_name='字段', db_constraint=False)
    is_query = models.BooleanField(default=1, verbose_name='是否可查询')
    is_create = models.BooleanField(default=1, verbose_name='是否可创建')
    is_update = models.BooleanField(default=1, verbose_name='是否可更新')

    class Meta:
        db_table = table_prefix + "system_field_permission"
        verbose_name = "字段权限表"
        verbose_name_plural = verbose_name
        ordering = ("id",)


class MenuButton(CoreModel):
    menu = models.ForeignKey(
        to="Menu",
        db_constraint=False,
        related_name="menuPermission",
        on_delete=models.CASCADE,
        verbose_name="关联菜单",
        help_text="关联菜单",
    )
    name = models.CharField(max_length=64, verbose_name="名称", help_text="名称")
    value = models.CharField(unique=True, max_length=64, verbose_name="权限值", help_text="权限值")
    api = models.CharField(max_length=200, verbose_name="接口地址", help_text="接口地址")
    METHOD_CHOICES = (
        (0, "GET"),
        (1, "POST"),
        (2, "PUT"),
        (3, "DELETE"),
    )
    method = models.IntegerField(default=0, verbose_name="接口请求方法", null=True, blank=True,
                                 help_text="接口请求方法")

    class Meta:
        db_table = table_prefix + "system_menu_button"
        verbose_name = "菜单权限表"
        verbose_name_plural = verbose_name
        ordering = ("-name",)


class RoleMenuPermission(CoreModel):
    role = models.ForeignKey(
        to="Role",
        db_constraint=False,
        related_name="role_menu",
        on_delete=models.CASCADE,
        verbose_name="关联角色",
        help_text="关联角色",
    )
    menu = models.ForeignKey(
        to="Menu",
        db_constraint=False,
        related_name="role_menu",
        on_delete=models.CASCADE,
        verbose_name="关联菜单",
        help_text="关联菜单",
    )

    class Meta:
        db_table = table_prefix + "role_menu_permission"
        verbose_name = "角色菜单权限表"
        verbose_name_plural = verbose_name
        # ordering = ("-create_datetime",)


class RoleMenuButtonPermission(CoreModel):
    role = models.ForeignKey(
        to="Role",
        db_constraint=False,
        related_name="role_menu_button",
        on_delete=models.CASCADE,
        verbose_name="关联角色",
        help_text="关联角色",
    )
    menu_button = models.ForeignKey(
        to="MenuButton",
        db_constraint=False,
        related_name="menu_button_permission",
        on_delete=models.CASCADE,
        verbose_name="关联菜单按钮",
        help_text="关联菜单按钮",
        null=True,
        blank=True
    )
    DATASCOPE_CHOICES = (
        (0, "仅本人数据权限"),
        (1, "本部门及以下数据权限"),
        (2, "本部门数据权限"),
        (3, "全部数据权限"),
        (4, "自定数据权限"),
    )
    data_range = models.IntegerField(default=0, choices=DATASCOPE_CHOICES, verbose_name="数据权限范围",
                                     help_text="数据权限范围")
    dept = models.ManyToManyField(to="Dept", blank=True, verbose_name="数据权限-关联部门", db_constraint=False,
                                  help_text="数据权限-关联部门")

    class Meta:
        db_table = table_prefix + "role_menu_button_permission"
        verbose_name = "角色按钮权限表"
        verbose_name_plural = verbose_name
        ordering = ("-create_datetime",)


class Dictionary(CoreModel):
    TYPE_LIST = (
        (0, "text"),
        (1, "number"),
        (2, "date"),
        (3, "datetime"),
        (4, "time"),
        (5, "files"),
        (6, "boolean"),
        (7, "images"),
    )
    label = models.CharField(max_length=100, blank=True, null=True, verbose_name="字典名称", help_text="字典名称")
    value = models.CharField(max_length=200, blank=True, null=True, verbose_name="字典编号", help_text="字典编号/实际值")
    parent = models.ForeignKey(
        to="self",
        related_name="sublist",
        db_constraint=False,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name="父级",
        help_text="父级",
    )
    type = models.IntegerField(choices=TYPE_LIST, default=0, verbose_name="数据值类型", help_text="数据值类型")
    color = models.CharField(max_length=20, blank=True, null=True, verbose_name="颜色", help_text="颜色")
    is_value = models.BooleanField(default=False, verbose_name="是否为value值",
                                   help_text="是否为value值,用来做具体值存放")
    status = models.BooleanField(default=True, verbose_name="状态", help_text="状态")
    sort = models.IntegerField(default=1, verbose_name="显示排序", null=True, blank=True, help_text="显示排序")
    remark = models.CharField(max_length=2000, blank=True, null=True, verbose_name="备注", help_text="备注")

    class Meta:
        db_table = table_prefix + "system_dictionary"
        verbose_name = "字典表"
        verbose_name_plural = verbose_name
        ordering = ("sort",)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)
        dispatch.refresh_dictionary()  # 有更新则刷新字典配置

    def delete(self, using=None, keep_parents=False):
        res = super().delete(using, keep_parents)
        dispatch.refresh_dictionary()
        return res


class OperationLog(CoreModel):
    request_modular = models.CharField(max_length=64, verbose_name="请求模块", null=True, blank=True,
                                       help_text="请求模块")
    request_path = models.CharField(max_length=400, verbose_name="请求地址", null=True, blank=True,
                                    help_text="请求地址")
    request_body = models.TextField(verbose_name="请求参数", null=True, blank=True, help_text="请求参数")
    request_method = models.CharField(max_length=8, verbose_name="请求方式", null=True, blank=True,
                                      help_text="请求方式")
    request_msg = models.TextField(verbose_name="操作说明", null=True, blank=True, help_text="操作说明")
    request_ip = models.CharField(max_length=32, verbose_name="请求ip地址", null=True, blank=True,
                                  help_text="请求ip地址")
    request_browser = models.CharField(max_length=64, verbose_name="请求浏览器", null=True, blank=True,
                                       help_text="请求浏览器")
    response_code = models.CharField(max_length=32, verbose_name="响应状态码", null=True, blank=True,
                                     help_text="响应状态码")
    request_os = models.CharField(max_length=64, verbose_name="操作系统", null=True, blank=True, help_text="操作系统")
    json_result = models.TextField(verbose_name="返回信息", null=True, blank=True, help_text="返回信息")
    status = models.BooleanField(default=False, verbose_name="响应状态", help_text="响应状态")

    class Meta:
        db_table = table_prefix + "system_operation_log"
        verbose_name = "操作日志"
        verbose_name_plural = verbose_name
        ordering = ("-create_datetime",)


def media_file_name(instance, filename):
    h = instance.md5sum
    basename, ext = os.path.splitext(filename)
    return os.path.join("files", h[:1], h[1:2], h + ext.lower())


class FileList(CoreModel):
    name = models.CharField(max_length=200, null=True, blank=True, verbose_name="名称", help_text="名称")
    url = models.FileField(upload_to=media_file_name, null=True, blank=True,)
    file_url = models.CharField(max_length=255, blank=True, verbose_name="文件地址", help_text="文件地址")
    engine = models.CharField(max_length=100, default='local', blank=True, verbose_name="引擎", help_text="引擎")
    mime_type = models.CharField(max_length=100, blank=True, verbose_name="Mime类型", help_text="Mime类型")
    size = models.CharField(max_length=36, blank=True, verbose_name="文件大小", help_text="文件大小")
    md5sum = models.CharField(max_length=36, blank=True, verbose_name="文件md5", help_text="文件md5")
    UPLOAD_METHOD_CHOIDES = (
        (0, '默认上传'),
        (1, '文件选择器上传'),
    )
    upload_method = models.SmallIntegerField(default=0, blank=True, null=True, choices=UPLOAD_METHOD_CHOIDES, verbose_name='上传方式', help_text='上传方式')
    FILE_TYPE_CHOIDES = (
        (0, '图片'),
        (1, '视频'),
        (2, '音频'),
        (3, '其他'),
    )
    file_type = models.SmallIntegerField(default=3, choices=FILE_TYPE_CHOIDES, blank=True, null=True, verbose_name='文件类型', help_text='文件类型')

    def save(self, *args, **kwargs):
        if not self.md5sum:  # file is new
            md5 = hashlib.md5()
            for chunk in self.url.chunks():
                md5.update(chunk)
            self.md5sum = md5.hexdigest()
        if not self.size:
            self.size = self.url.size
        if not self.file_url:
            url = media_file_name(self, self.name)
            self.file_url = f'media/{url}'
        super(FileList, self).save(*args, **kwargs)

    class Meta:
        db_table = table_prefix + "system_file_list"
        verbose_name = "文件管理"
        verbose_name_plural = verbose_name
        ordering = ("-create_datetime",)


class Area(CoreModel):
    name = models.CharField(max_length=100, verbose_name="名称", help_text="名称")
    code = models.CharField(max_length=20, verbose_name="地区编码", help_text="地区编码", unique=True, db_index=True)
    level = models.BigIntegerField(verbose_name="地区层级(1省份 2城市 3区县 4乡级)",
                                   help_text="地区层级(1省份 2城市 3区县 4乡级)")
    pinyin = models.CharField(max_length=255, verbose_name="拼音", help_text="拼音")
    initials = models.CharField(max_length=20, verbose_name="首字母", help_text="首字母")
    enable = models.BooleanField(default=True, verbose_name="是否启用", help_text="是否启用")
    pcode = models.ForeignKey(
        to="self",
        verbose_name="父地区编码",
        to_field="code",
        on_delete=models.CASCADE,
        db_constraint=False,
        null=True,
        blank=True,
        help_text="父地区编码",
    )

    class Meta:
        db_table = table_prefix + "system_area"
        verbose_name = "地区表"
        verbose_name_plural = verbose_name
        ordering = ("code",)

    def __str__(self):
        return f"{self.name}"


class ApiWhiteList(CoreModel):
    url = models.CharField(max_length=200, help_text="url地址", verbose_name="url")
    METHOD_CHOICES = (
        (0, "GET"),
        (1, "POST"),
        (2, "PUT"),
        (3, "DELETE"),
    )
    method = models.IntegerField(default=0, verbose_name="接口请求方法", null=True, blank=True,
                                 help_text="接口请求方法")
    enable_datasource = models.BooleanField(default=True, verbose_name="激活数据权限", help_text="激活数据权限",
                                            blank=True)

    class Meta:
        db_table = table_prefix + "api_white_list"
        verbose_name = "接口白名单"
        verbose_name_plural = verbose_name
        ordering = ("-create_datetime",)


class SystemConfig(CoreModel):
    """
    系统配置模型类 - Django ORM模型定义
    
    这个类确实定义了数据库表字段与Python对象属性的映射关系。
    Django ORM (Object-Relational Mapping) 使用这种方式实现：
    1. 数据库表结构定义
    2. Python对象与数据库记录的双向映射
    3. 数据验证和类型转换
    4. 数据库操作的高级抽象
    
    当Django执行migration时，会根据这个模型类的字段定义在数据库中创建对应的表和列。
    
    数据库表名：table_prefix + "system_config" (通常为 "dvadmin_system_config")
    
    字段名定义：
    1. parent - 父级配置项ID (外键关联自身)
    2. title - 配置项标题 (varchar(50))
    3. key - 配置项键名 (varchar(100), 带索引)
    4. value - 配置项的值 (JSON格式)
    5. sort - 排序序号 (integer)
    6. status - 启用状态 (boolean)
    7. data_options - 数据选项 (JSON格式)
    8. form_item_type - 表单类型 (integer, 带choices选项)
    9. rule - 校验规则 (JSON格式)
    10. placeholder - 提示信息 (varchar(50))
    11. setting - 其他配置 (JSON格式)
    
    继承字段 (来自CoreModel基类):
    - id - 主键ID (自增)
    - create_datetime - 创建时间
    - update_datetime - 更新时间
    - description - 描述信息
    - creator_id - 创建者ID
    - modifier_id - 修改者ID
    """
    
    # 系统配置的父子关系字段定义
    # 字段名：parent
    # 数据库列名：parent_id
    # 数据类型：integer (外键)
    parent = models.ForeignKey(
        to="self",                    # 指向自身模型，实现自关联
        verbose_name="父级",           # 在Django管理后台显示的字段名称
        on_delete=models.CASCADE,     # 删除父级时，级联删除所有子级配置
        db_constraint=False,          # 不在数据库层面创建外键约束，由Django应用层管理
        null=True,                    # 数据库层面允许为空值
        blank=True,                   # 表单验证层面允许为空
        help_text="父级",             # 字段的帮助文本，用于表单提示
    )
    
    # 配置项标题字段
    # 字段名：title
    # 数据库列名：title
    # 数据类型：varchar(50)
    title = models.CharField(max_length=50, verbose_name="标题", help_text="标题")
    
    # 配置项键名字段
    # 字段名：key
    # 数据库列名：key
    # 数据类型：varchar(100) 带索引
    key = models.CharField(max_length=100, verbose_name="键", help_text="键", db_index=True)
    
    # 配置项的值字段
    # 字段名：value
    # 数据库列名：value
    # 数据类型：JSON
    value = models.JSONField(max_length=100, verbose_name="值", help_text="值", null=True, blank=True)
    
    # 排序字段
    # 字段名：sort
    # 数据库列名：sort
    # 数据类型：integer
    sort = models.IntegerField(default=0, verbose_name="排序", help_text="排序", blank=True)
    
    # 启用状态字段
    # 字段名：status
    # 数据库列名：status
    # 数据类型：boolean
    status = models.BooleanField(default=True, verbose_name="启用状态", help_text="启用状态")
    
    # 数据选项字段
    # 字段名：data_options
    # 数据库列名：data_options
    # 数据类型：JSON
    data_options = models.JSONField(verbose_name="数据options", help_text="数据options", null=True, blank=True)
    
    # 表单类型选择列表 - 定义了支持的所有表单控件类型
    # 这是Django choices的标准用法：元组列表，每个元组包含(存储值, 显示名称)
    FORM_ITEM_TYPE_LIST = (
        (0, "text"),         # 文本输入框
        (1, "datetime"),     # 日期时间选择器
        (2, "date"),         # 日期选择器
        (3, "textarea"),     # 多行文本域
        (4, "select"),       # 下拉选择框
        (5, "checkbox"),     # 复选框
        (6, "radio"),        # 单选按钮
        (7, "img"),          # 图片上传
        (8, "file"),         # 文件上传
        (9, "switch"),       # 开关切换
        (10, "number"),      # 数字输入
        (11, "array"),       # 数组类型
        (12, "imgs"),        # 多图片上传
        (13, "foreignkey"),  # 外键关联
        (14, "manytomany"),  # 多对多关联
        (15, "time"),        # 时间选择器
    )
    
    # 表单类型字段
    # 字段名：form_item_type
    # 数据库列名：form_item_type
    # 数据类型：integer
    form_item_type = models.IntegerField(
        choices=FORM_ITEM_TYPE_LIST, verbose_name="表单类型", help_text="表单类型", default=0, blank=True
    )
    
    # 校验规则字段
    # 字段名：rule
    # 数据库列名：rule
    # 数据类型：JSON
    rule = models.JSONField(null=True, blank=True, verbose_name="校验规则", help_text="校验规则")
    
    # 提示信息字段
    # 字段名：placeholder
    # 数据库列名：placeholder
    # 数据类型：varchar(50)
    placeholder = models.CharField(max_length=50, null=True, blank=True, verbose_name="提示信息", help_text="提示信息")
    
    # 其他配置字段
    # 字段名：setting
    # 数据库列名：setting
    # 数据类型：JSON
    setting = models.JSONField(null=True, blank=True, verbose_name="配置", help_text="配置")

    class Meta:
        """
        Django Model的元数据配置类
        
        Meta类是Django模型的内置配置类，用于定义模型的各种元数据选项，包括：
        
        1. 数据库相关配置：
           - db_table: 指定数据库表名，而不是使用Django的默认命名规则
           - ordering: 指定查询时的默认排序规则
           - indexes: 定义数据库索引
           - constraints: 定义数据库约束
        
        2. 管理界面配置：
           - verbose_name: 模型在Django管理后台的单数显示名称
           - verbose_name_plural: 模型在Django管理后台的复数显示名称
        
        3. 查询和权限配置：
           - permissions: 自定义权限
           - default_permissions: 默认权限设置
           - get_latest_by: 指定获取最新记录的字段
        
        4. 唯一性约束：
           - unique_together: 联合唯一约束
        
        Meta类的作用：
        - 不会创建数据库字段，只是提供模型的元信息
        - 影响Django ORM的行为和数据库表的结构
        - 控制Django管理后台的显示效果
        - 定义数据库层面的约束和索引
        """
        
        # 指定数据库表名，table_prefix是全局变量，用于统一表名前缀
        db_table = table_prefix + "system_config"
        
        # Django管理后台显示的模型名称（单数形式）
        verbose_name = "系统配置表"
        
        # Django管理后台显示的模型名称（复数形式）
        # 这里设置为与单数相同，符合中文习惯
        verbose_name_plural = verbose_name
        
        # 默认排序规则 - 按sort字段升序排列
        # 所有查询操作默认会按这个顺序返回结果
        ordering = ("sort",)
        
        # 联合唯一约束 - key和parent_id的组合必须唯一
        # 这确保了在同一个父级下，不能有重复的key值
        # 但不同父级下可以有相同的key值
        unique_together = (("key", "parent_id"),)

    def __str__(self):
        """
        模型的字符串表示方法
        
        当需要将模型实例转换为字符串时调用（如在Django管理后台显示）
        返回配置项的标题作为对象的可读表示
        """
        return f"{self.title}"

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        重写保存方法，添加配置更新后的缓存刷新逻辑
        
        当系统配置被保存（新增或修改）时，自动刷新应用程序中的配置缓存，
        确保程序使用的是最新的配置数据
        """
        # 调用父类的保存方法，执行实际的数据库保存操作
        super().save(force_insert, force_update, using, update_fields)
        
        # 刷新系统配置缓存，确保应用程序获取到最新配置
        dispatch.refresh_system_config()

    def delete(self, using=None, keep_parents=False):
        """
        重写删除方法，添加配置删除后的缓存刷新逻辑
        
        当系统配置被删除时，自动刷新应用程序中的配置缓存，
        确保被删除的配置不再被程序使用
        """
        # 调用父类的删除方法，执行实际的数据库删除操作
        res = super().delete(using, keep_parents)
        
        # 刷新系统配置缓存，清除已删除的配置项
        dispatch.refresh_system_config()
        
        return res


class LoginLog(CoreModel):
    LOGIN_TYPE_CHOICES = ((1, "普通登录"), (2, "微信扫码登录"),)
    username = models.CharField(max_length=32, verbose_name="登录用户名", null=True, blank=True, help_text="登录用户名")
    ip = models.CharField(max_length=32, verbose_name="登录ip", null=True, blank=True, help_text="登录ip")
    agent = models.TextField(verbose_name="agent信息", null=True, blank=True, help_text="agent信息")
    browser = models.CharField(max_length=200, verbose_name="浏览器名", null=True, blank=True, help_text="浏览器名")
    os = models.CharField(max_length=200, verbose_name="操作系统", null=True, blank=True, help_text="操作系统")
    continent = models.CharField(max_length=50, verbose_name="州", null=True, blank=True, help_text="州")
    country = models.CharField(max_length=50, verbose_name="国家", null=True, blank=True, help_text="国家")
    province = models.CharField(max_length=50, verbose_name="省份", null=True, blank=True, help_text="省份")
    city = models.CharField(max_length=50, verbose_name="城市", null=True, blank=True, help_text="城市")
    district = models.CharField(max_length=50, verbose_name="县区", null=True, blank=True, help_text="县区")
    isp = models.CharField(max_length=50, verbose_name="运营商", null=True, blank=True, help_text="运营商")
    area_code = models.CharField(max_length=50, verbose_name="区域代码", null=True, blank=True, help_text="区域代码")
    country_english = models.CharField(max_length=50, verbose_name="英文全称", null=True, blank=True,
                                       help_text="英文全称")
    country_code = models.CharField(max_length=50, verbose_name="简称", null=True, blank=True, help_text="简称")
    longitude = models.CharField(max_length=50, verbose_name="经度", null=True, blank=True, help_text="经度")
    latitude = models.CharField(max_length=50, verbose_name="纬度", null=True, blank=True, help_text="纬度")
    login_type = models.IntegerField(default=1, choices=LOGIN_TYPE_CHOICES, verbose_name="登录类型",
                                     help_text="登录类型")

    class Meta:
        db_table = table_prefix + "system_login_log"
        verbose_name = "登录日志"
        verbose_name_plural = verbose_name
        ordering = ("-create_datetime",)


class MessageCenter(CoreModel):
    title = models.CharField(max_length=100, verbose_name="标题", help_text="标题")
    content = models.TextField(verbose_name="内容", help_text="内容")
    target_type = models.IntegerField(default=0, verbose_name="目标类型", help_text="目标类型")
    target_user = models.ManyToManyField(to=Users, related_name='user', through='MessageCenterTargetUser',
                                         through_fields=('messagecenter', 'users'), blank=True, verbose_name="目标用户",
                                         help_text="目标用户")
    target_dept = models.ManyToManyField(to=Dept, blank=True, db_constraint=False,
                                         verbose_name="目标部门", help_text="目标部门")
    target_role = models.ManyToManyField(to=Role, blank=True, db_constraint=False,
                                         verbose_name="目标角色", help_text="目标角色")

    class Meta:
        db_table = table_prefix + "message_center"
        verbose_name = "消息中心"
        verbose_name_plural = verbose_name
        ordering = ("-create_datetime",)


class MessageCenterTargetUser(CoreModel):
    users = models.ForeignKey(Users, related_name="target_user", on_delete=models.CASCADE, db_constraint=False,
                              verbose_name="关联用户表", help_text="关联用户表")
    messagecenter = models.ForeignKey(MessageCenter, on_delete=models.CASCADE, db_constraint=False,
                                      verbose_name="关联消息中心表", help_text="关联消息中心表")
    is_read = models.BooleanField(default=False, blank=True, null=True, verbose_name="是否已读", help_text="是否已读")

    class Meta:
        db_table = table_prefix + "message_center_target_user"
        verbose_name = "消息中心目标用户表"
        verbose_name_plural = verbose_name


def media_file_name_downloadcenter(instance:'DownloadCenter', filename):
    h = instance.md5sum
    basename, ext = os.path.splitext(filename)
    return PurePosixPath("files", "dlct", h[:1], h[1:2], basename + '-' + str(time()).replace('.', '') + ext.lower())


class DownloadCenter(CoreModel):
    TASK_STATUS_CHOICES = [
        (0, '任务已创建'),
        (1, '任务进行中'),
        (2, '任务完成'),
        (3, '任务失败'),
    ]
    task_name = models.CharField(max_length=255, verbose_name="任务名称", help_text="任务名称")
    task_status = models.SmallIntegerField(default=0, choices=TASK_STATUS_CHOICES, verbose_name='是否可下载', help_text='是否可下载')
    file_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="文件名", help_text="文件名")
    url = models.FileField(upload_to=media_file_name_downloadcenter, null=True, blank=True)
    size = models.BigIntegerField(default=0, verbose_name="文件大小", help_text="文件大小")
    md5sum = models.CharField(max_length=36, null=True, blank=True, verbose_name="文件md5", help_text="文件md5")

    def save(self, *args, **kwargs):
        if self.url:
            if not self.md5sum:  # file is new
                md5 = hashlib.md5()
                for chunk in self.url.chunks():
                    md5.update(chunk)
                self.md5sum = md5.hexdigest()
            if not self.size:
                self.size = self.url.size
        super(DownloadCenter, self).save(*args, **kwargs)

    class Meta:
        db_table = table_prefix + "download_center"
        verbose_name = "下载中心"
        verbose_name_plural = verbose_name
        ordering = ("-create_datetime",)
