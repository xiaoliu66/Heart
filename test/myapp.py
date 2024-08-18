import os
import sys
import time

from flask import Flask, render_template_string
from flask import render_template  # 渲染
from diskcache import Cache

app = Flask(__name__)


@app.route('/')  # 主页地址,“装饰器”
def news():
    return render_template('index.html')  # 把index.html文件读进来，再交给浏览器


@app.route('/getHeartNum', methods=['get'])
def getHeartNum():
    cache = Cache('/cache')
    value = cache.get('value')
    maxValue = cache.get('maxValue')
    minValue = cache.get('minValue')

    heartInfo = {'value': value, 'maxValue': maxValue, 'minValue': minValue}
    print(heartInfo)
    return heartInfo


def main(port):
    print('========' + port)
    print(os.getcwd())  # 获取当前工作目录路径
    print(os.path.abspath('..'))  # 获取当前工作目录路径
    app.run(host='127.0.0.1', debug=True, port=port, use_reloader=False)  # 127.0.0.1 回路 自己返回自己


# def exit():
#     # os._exit(0)
#     # sys.exit(0)
#     exit()

if __name__ == '__main__':
    # cache = Cache('/cache')
    main()
