import multiprocessing  # 导入多进程模块，用于设置工作进程数
import os  # 导入操作系统接口模块，用于获取当前工作目录和平台信息
import sys  # 导入系统特定的参数和函数模块，用于操作Python路径

# 获取当前工作目录的绝对路径
root_path = os.getcwd()
# 将项目根目录添加到Python模块搜索路径中，确保能够正确导入项目模块
sys.path.append(root_path)
import uvicorn  # 导入uvicorn ASGI服务器，用于运行Django应用
from application.settings import LOGGING  # 从项目设置中导入日志配置

if __name__ == '__main__':
    # 在Windows平台下，multiprocessing模块需要调用freeze_support()来支持打包后的可执行文件
    multiprocessing.freeze_support()
    
    # 设置默认工作进程数为4，适用于多核CPU环境提高并发处理能力
    workers = 4
    
    # 检查当前操作系统平台
    if os.sys.platform.startswith('win'):
        # Windows操作系统下设置workers为None，使用单进程模式
        # 因为Windows的多进程支持与Unix/Linux不同，容易出现问题
        workers = None
    
    # 启动uvicorn ASGI服务器
    uvicorn.run(
        "application.asgi:application",  # 指定ASGI应用的位置：模块路径.应用对象
        reload=False,  # 禁用自动重载功能，生产环境不需要文件变化时自动重启
        host="0.0.0.0",  # 绑定所有可用的网络接口，允许外部访问
        port=8000,  # 设置服务器监听端口为8000
        workers=workers,  # 工作进程数，Windows下为None(单进程)，其他系统为4
        log_config=LOGGING  # 使用Django项目中配置的日志设置
    )
