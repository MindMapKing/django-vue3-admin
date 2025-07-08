# 常见Python魔法变量及其作用：
# __all__     ：控制 from xxx import * 时能被导入的成员列表。
# __version__ ：标记模块或包的版本号，便于工具或用户识别。
# __author__  ：标记作者信息，方便文档和工具读取。
# __doc__     ：模块的文档字符串，Python解释器会自动识别。
# __file__    ：当前模块文件的绝对路径，Python自动赋值。
# __name__    ：当前模块名，Python自动赋值。
# __path__    ：包的搜索路径，仅在包的 __init__.py 中出现，Python自动赋值。
# 这些魔法变量必须严格按照官方命名，不能随意更改，否则不会被Python识别和使用。

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

# __all__ 详解：
# __all__ = ('celery_app',) 是一个元组，定义了当使用 from application import * 时
# 能够被导入的公共接口。
# 
# 具体作用：
# 1. 控制导入范围：只有列在 __all__ 中的名称才会被 import * 导入
# 2. 明确公共API：告诉使用者这个模块对外提供哪些接口
# 3. 避免内部实现泄露：防止私有变量或内部函数被意外导入
#
# 在这个例子中：
# - celery_app 是从 .celery 模块导入的 Celery 应用实例
# - 通过 __all__ 声明，使得其他模块可以通过 from application import * 获取到 celery_app
# - 这对于 Django + Celery 集成很重要，确保 Celery 应用在 Django 启动时被正确初始化
# 
# 注意：元组只有一个元素时，末尾的逗号不能省略，否则会被解释为普通的括号表达式
__all__ = ('celery_app',)