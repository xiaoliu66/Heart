from flask import Flask
from flask import render_template  # 渲染
from diskcache import Cache


app = Flask(__name__)


@app.route('/')  # 主页地址,“装饰器”
def news():
    return render_template('index.html')  # 把index.html文件读进来，再交给浏览器


@app.route('/getHeartNum', methods=['get'])
def getHeartNum():
    value = cache.get('value')
    maxValue = cache.get('maxValue')
    minValue = cache.get('minValue')

    heartInfo = {'value': value, 'maxValue': maxValue, 'minValue': minValue}
    print(heartInfo)
    return heartInfo


if __name__ == '__main__':
    cache = Cache('/cache')
    app.run(host='127.0.0.1', debug=True, port=80)  # 127.0.0.1 回路 自己返回自己
