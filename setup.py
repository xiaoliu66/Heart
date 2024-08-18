from cx_Freeze import setup, Executable
import sys

sys.setrecursionlimit(5000)
# 入口点
entry_point = 'main.py'

# 主程序手动命名
target_name = 'heart.exe'

files = ['static/', 'templates/', 'util/', 'web/']

# 打包选项
options = {
    'build_exe': {
        'include_files': files,  # 需要包含的其他文件
        'packages': ['uvicorn', 'diskcache', 'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtWebChannel',
                     'PyQt5.QtWebEngineWidgets', 'bleak', 'fastapi'],  # 需要包含的依赖库
        "zip_include_packages": ['uvicorn', 'diskcache', 'bleak', 'fastapi'],
        # 剔除不需要的包
        "excludes": ['tkinter', 'numpy', 'pandas', 'matplotlib', 'numpydoc', 'OpenSSL', 'paramiko', 'tornado',
                     'chardet', 'docutils', 'email', 'jupyter', 'urllib3', 'yaml', 'zmq', 'jedi',
                     'requests', 'pygments', 'pillow', 'jupyter_client', 'jupyter_core', 'ipython'],

    },
}

# 创建可执行文件
setup(
    name='Heart',
    version='1.0',
    description='心跳连接器',
    options=options,
    # executables=[Executable(entry_point, base="Win32GUI")] # 加了base 程序运行后没有日志窗口
    executables=[Executable(entry_point, base="Win32GUI", icon="static/heart.ico")]
)
