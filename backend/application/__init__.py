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

__all__ = ('celery_app',)