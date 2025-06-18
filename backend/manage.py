#!/usr/bin/env python
"""
Django项目的命令行管理工具脚本
提供了Django项目的各种管理命令，如runserver、migrate、makemigrations等
"""
import os  # 导入操作系统接口模块，用于环境变量操作和系统交互
import sys  # 导入系统特定的参数和函数模块，用于访问命令行参数和Python解释器相关功能


def main():
    """
    运行Django管理任务的主函数
    负责设置Django环境并执行命令行操作
    """
    # 设置Django设置模块的环境变量，如果未设置则使用默认值'application.settings'
    # 这告诉Django在哪里查找项目的配置文件
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings')
    
    try:
        # 尝试从Django核心管理模块导入命令行执行函数
        # 这个函数负责解析和执行所有Django管理命令
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # 如果导入失败，说明Django未正确安装或环境配置有问题
        raise ImportError(
            "无法导入Django。请确保Django已正确安装并且 "
            "在PYTHONPATH环境变量中可用。是否忘记激活虚拟环境？"
        ) from exc  # 保留原始异常信息，便于调试
    
    # 执行Django命令行工具，sys.argv包含了所有命令行参数
    # 例如：python manage.py runserver 8000
    # sys.argv = ['manage.py', 'runserver', '8000']
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    # 当该脚本作为主程序运行时（而不是被导入时），执行main函数
    # 这是Python脚本的标准入口点检查
    main()
