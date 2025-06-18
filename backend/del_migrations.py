# -*- coding: utf-8 -*-
"""
Django项目迁移文件清理脚本
用于删除项目中所有的数据库迁移文件（保留__init__.py文件）
注意：此脚本仅建议在开发环境使用，使用前请备份数据库！
"""

import os  # 导入操作系统接口模块，用于文件和目录操作

# 定义需要排除的目录列表，避免删除虚拟环境等重要目录中的文件
exclude = ["venv"]  # 排除虚拟环境目录，可根据需要添加其他目录如["venv", "env", ".venv"]

# 使用os.walk()遍历当前目录及所有子目录
# root: 当前遍历的目录路径
# dirs: 当前目录下的所有子目录列表
# files: 当前目录下的所有文件列表
for root, dirs, files in os.walk('.'):
    # 从dirs列表中排除不需要处理的目录
    # 使用集合运算去除排除列表中的目录，确保不会进入这些目录进行处理
    # dirs[:] 是Python中的切片赋值语法，用于就地修改列表内容
    # 与直接赋值 dirs = ... 不同的是：
    # dirs[:] 会保持原列表对象不变，只替换其内容
    # 这样os.walk()仍能正确识别目录过滤，因为它引用的是同一个列表对象
    # 
    # 工作原理：
    # 1. set(dirs) - 将目录列表转换为集合
    # 2. set(exclude) - 将排除目录列表转换为集合  
    # 3. set(dirs) - set(exclude) - 集合差集运算，移除需要排除的目录
    # 4. list(...) - 将结果转换回列表
    # 5. dirs[:] = ... - 切片赋值，就地替换dirs列表的所有元素（重新赋值）
    dirs[:] = list(set(dirs) - set(exclude))
    
    # 检查当前目录列表中是否包含'migrations'目录
    if 'migrations' in dirs:
        # 获取migrations目录名（通常就是'migrations'）
        dir = dirs[dirs.index('migrations')]
        
        # 遍历migrations目录及其子目录中的所有文件
        # root_j: migrations目录的路径
        # dirs_j: migrations目录下的子目录列表
        # files_j: migrations目录下的文件列表
        for root_j, dirs_j, files_j in os.walk(os.path.join(root, dir)):
            # 遍历migrations目录中的每个文件
            for file_k in files_j:
                # 保留__init__.py文件，这个文件是Python包的标识文件，不能删除
                if file_k != '__init__.py':
                    # 构建完整的文件路径
                    dst_file = os.path.join(root_j, file_k)
                    # 输出将要删除的文件路径，便于用户确认操作
                    print('删除文件>>> ', dst_file)
                    # 删除迁移文件
                    os.remove(dst_file)