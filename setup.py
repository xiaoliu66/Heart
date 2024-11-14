from cx_Freeze import setup, Executable
import sys

sys.setrecursionlimit(5000)
# 入口点
entry_point = 'heart.py'

# 主程序手动命名
target_name = 'heart.exe'

files = ['static/', 'templates/', 'util/', 'web/']

# 打包选项
options = {
    'build_exe': {
        'build_exe': 'heart',  # 编译输出的文件目录
        'include_files': files,  # 需要包含的其他文件
        'packages': ['PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtWebChannel', 'PyQt5.QtWebEngineWidgets','uvicorn',
                     'diskcache',  'bleak', 'fastapi', 'loguru'],  # 需要包含的依赖库
        "zip_include_packages": ['uvicorn', 'diskcache', 'bleak', 'fastapi'],
        # 剔除不需要的包 (这个根据自己的本地依赖包情况来看，如果安装了anaconda3 就需要排除很多的包，不然打包后的体积非常惊人 6.34GB)
        # 剔除了tzdata, 打包目录下就会出现zoneinfo 时区转换这个库。
        "excludes": ['tkinter', 'numpy', 'pandas', 'matplotlib', 'numpydoc', 'OpenSSL', 'paramiko', 'tornado',
                     'chardet', 'docutils', 'email', 'jupyter', 'urllib3', 'yaml', 'zmq', 'jedi',
                     'requests', 'pygments', 'pillow', 'jupyter_client', 'jupyter_core', 'ipython', 'debugpy',
                     'tzdata'],

    },
}

# 创建可执行文件
setup(
    name='Heart',
    version='1.0',
    description='心率记录器',
    options=options,
    # executables=[Executable(entry_point, base="Win32GUI")] # 加了base 程序运行后没有日志窗口
    executables=[Executable(entry_point, icon="static/heart.ico")]
    # executables=[Executable(entry_point, base="Win32GUI", icon="static/heart.ico")]
)
