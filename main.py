import ctypes
import inspect
from loguru import logger
import sys
import os
import threading
import urllib.request
import warnings

from PyQt5 import QtGui
from diskcache import Cache
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QObject, pyqtSlot, QUrl, Qt
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView

import asyncio
from bleak import BleakScanner, BleakClient, BleakGATTCharacteristic

import fastApi
from util.MyWebsocketServer import MyWebsocketServer

from util.ConfigUtil import *

warnings.filterwarnings("ignore", category=DeprecationWarning)

logger.add("application.log", rotation="50MB", encoding="utf-8", enqueue=True, level="DEBUG")
# 设备的Characteristic UUID
par_notification_characteristic = "00002a37-0000-1000-8000-00805f9b34fb"
# par_notification_characteristic = "ebe0ccc1-7a0a-4b0c-8a1a-6ff2997da3a6"
# 设备的MAC地址
# device_address = "C8:06:E2:3C:E1:91"
device_address = ""


# 搜索蓝牙设备信息 官网不建议用
# 这些方法对于简单的程序来说很方便，但不建议用于 更高级的用例，如长时间运行的程序、GUI 或连接到 多个设备。
async def searchBluetoothDevices():
    devices = await BleakScanner.discover()
    list = [];
    for d in devices:
        name = ''
        if (d.name is not None):
            name = d.name

        bluetooth_info = {"address": d.address, "name": name}
        logger.info(bluetooth_info)
        list.append(bluetooth_info)
    logger.info(list)
    return json.dumps(list)


# 实时获取心跳值
async def notification_handler(characteristic: BleakGATTCharacteristic, data: bytearray):
    global value

    # print("rev data:", data)   # 读取到的数据 rev data: bytearray(b'\x06V')
    # print("rev data:", int.from_bytes(data))

    #  rev data: bytearray(b'\x06\x82')
    # ❤: 130
    # bytearray(b'\x06T') 转换为十进制，我们首先需要理解这个字节串的含义。bytearray 表示一组字节，其中 \x06 和 \x54 是十六进制表示的两个字节。
    #
    #     1.\x06 对应的十进制值是 6。 暂时不知道这个值有啥用
    #     2.\x54 对应的十进制值是 84。  心跳的值， T 的ascii 的十六进制是54
    value = int(data.hex().split('06')[1], 16);
    cache.set('value', value)
    maxValue = cache.get('maxValue')
    minValue = cache.get('minValue')

    if maxValue == 0 and minValue == 0:
        cache.set('maxValue', value)
        cache.set('minValue', value)

    if value > maxValue:
        cache.set('maxValue', value)
    elif value < minValue:
        cache.set('minValue', value)

    # print('❤:', value)
    view.page().runJavaScript("window.getHeartNum('%s')" % value)
    return value
    # print(data.decode('ascii'))
    # print(data)


class CallHandler(QObject):

    def __init__(self):
        super(CallHandler, self).__init__()

    # 异步搜索附近的蓝牙设备信息
    @pyqtSlot(str)  # 第一个参数即为回调时携带的参数类型
    def initSearch(self, str_args):
        logger.info(f'------> initSearch......{str_args}')
        global search_thread
        search_thread = mySearchThread(11, "search-Thread", 0);
        search_thread.start()

        # msg = asyncio.run(searchBluetoothDevices())
        # view.page().runJavaScript("alert('%s')" % msg)
        # view.page().runJavaScript("window.initSearch('%s')" % msg)
        # info = '蓝牙设备连接成功！'
        # view.page().runJavaScript("window.get_info('%s')" % info)
        # return 'hello, Python'

    def getInfo(self):
        import socket, platform
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        list_info = platform.uname()
        sys_name = list_info[0] + list_info[2]
        cpu_name = list_info[5]
        dic_info = {"hostname": hostname, "ip": ip, "sys_name": sys_name, "cpu_name": cpu_name}
        # 调用js函数，实现回调
        # self.mainFrame.evaluateJavaScript('%s(%s)' % ('onGetInfo', json.dumps(dic_info)))
        return json.dumps(dic_info)

    # 接受前端传过来选择的蓝牙设备id进行连接
    @pyqtSlot(str, result=str)
    def connectBluetooth(self, str_args):
        logger.info(f'bluetooth {str_args} connecting......')
        words = str_args.split("#")
        uuid = "";
        if words[1] == "":
            uuid = par_notification_characteristic;
        else:
            uuid = words[1];
        device_address = words[0];
        logger.info('thread %s is running...' % threading.current_thread().name)
        global thread1
        logger.info(f'device_address is {device_address}, uuid is {uuid}')
        thread1 = myThread(1, "Thread-1", 0, device_address, uuid);
        try:
            thread1.start()
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            info = 'false'
            view.page().runJavaScript("window.getConnectInfo('%s')" % info)
        else:
            logger.info('----connectBluetooth---')
        # asyncio.run(self.startConnect(device_address))

    @pyqtSlot()
    def disconnectBluetooth(self):
        stop_thread(thread1)
        info = 'true'
        view.page().runJavaScript("window.stopConnect('%s')" % info)

    @pyqtSlot(result=int)
    def getHeartNum(self):
        logger.info(f"getHeartNum: {value}")
        view.page().runJavaScript("window.getHeartNum('%s')" % value)
        return value

    @pyqtSlot(str)
    def startServer(self, port):
        logger.info(f'----- startServer ----- port: {port}---')
        global server
        server = myServer(2, "Server-1", 0, port);
        try:
            server.start()
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            info = 'false'
            logger.info(info)
            view.page().runJavaScript("window.startServer('%s')" % info)
        else:
            info = 'true'
            logger.info(info)
            server.terminate()
            view.page().runJavaScript("window.startServer('%s')" % info)

    @pyqtSlot()
    def stopServer(self):
        logger.info('----- stopServer -----')
        # myapp.exit()
        stop_thread(server)
        info = 'true'
        view.page().runJavaScript("window.stopServer('%s')" % info)

    # 调用js代码，将搜索到的蓝牙信息返回给前端
    @pyqtSlot()
    def getBlueInfo(self):
        list = []
        data = cache.get("dict")
        if data is not None:
            stop_thread(search_thread)
            for key, value in data.items():
                bluetooth_info = {"address": key, "name": value}
                list.append(bluetooth_info)
            logger.info(f"list: {list}")
            view.page().runJavaScript("window.initSearch('%s')" % json.dumps(list))

    @pyqtSlot(str)
    def onSubmitConfig(self, data):
        logger.info(f'----- onSubmitConfig {data}-----')
        try:
            modify_config_file(data)
        except Exception as e:
            logger.error(f"onSubmitConfig An error occurred: {e}")
            info = 'false'
            view.page().runJavaScript("window.onSubmitConfig('%s')" % info)
        else:
            info = 'true'
            view.page().runJavaScript("window.onSubmitConfig('%s')" % info)

    @pyqtSlot(str)
    def onBackConfig(self):
        logger.info('----- onBackConfig-----')
        try:
            default_config()
        except Exception as e:
            logger.error(f"onBackConfig An error occurred: {e}")
            info = 'false'
            view.page().runJavaScript("window.onSubmitConfig('%s')" % info)
        else:
            info = 'true'
            view.page().runJavaScript("window.onSubmitConfig('%s')" % info)


class WebEngine(QWebEngineView):
    def __init__(self):
        super(WebEngine, self).__init__()
        self.setContextMenuPolicy(Qt.NoContextMenu)  # 设置右键菜单规则为自定义右键菜单
        # self.customContextMenuRequested.connect(self.showRightMenu)  # 这里加载并显示自定义右键菜单，我们重点不在这里略去了详细带吗
        self.setWindowTitle('心跳记录器')
        self.resize(1200, 800)
        # cp = QDesktopWidget().availableGeometry().center()
        # self.move(QPoint(cp.x() - self.width() / 2, cp.y() - self.height() / 2))

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '确认', '您确定要关闭窗口吗？',
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            webSocketServer.stopServer()
            event.accept()
        else:
            event.ignore()


# 开启另一个线程去搜索蓝牙设备 不阻塞主线程
class mySearchThread(threading.Thread):
    def __init__(self, threadID, name, delay):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.delay = delay

    def run(self):
        logger.info('thread %s is running...' % threading.current_thread().name)
        # self.result = asyncio.run(self.searchBluetoothDevices())
        asyncio.run(self.getOtherDeviceInfo())
        # print("msg：", self.result)

        # runJavaScript 不能在子线程中运行，否则程序会直接退出，也没有报错信息
        # view.page().runJavaScript("window.initSearch('%s')" % msg)

    # BleakScanner 官网给的例子 https://bleak.readthedocs.io/en/latest/api/scanner.html#bleak.BleakScanner
    async def getOtherDeviceInfo(self):
        stop_event = asyncio.Event()
        dict = {}
        cache.delete("list")

        # add something that calls stop_event.set()
        # result = cache.get("list")
        # while result is not None:
        #     stop_event.set()
        def callback(device, advertising_data):
            # do something with incoming data
            # print('device', device)

            name = ''
            if (device.name is not None):
                name = device.name

            dict.update({device.address: name})

            logger.info('dict----> {dict}', dict=dict)
            cache.set('dict', dict)

        async with BleakScanner(callback) as scanner:
            # list = scanner.discovered_devices
            # print(list)
            # Important! Wait for an event to trigger stop, otherwise scanner
            # will stop immediately.
            await stop_event.wait()


# 开启另一个线程去连接蓝牙 实时获取心跳值
class myThread(threading.Thread):
    d_address = "";

    def __init__(self, threadID, name, delay, bluetoothAdresss, uuid):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.delay = delay
        self.d_address = bluetoothAdresss;
        self.uuid = uuid;

    def run(self):
        logger.info('thread %s is running...' % threading.current_thread().name)
        asyncio.run(self.startConnect(self.d_address, self.uuid))

    async def startConnect(self, device_address, uuid):
        logger.info('thread %s is running...' % threading.current_thread().name)
        logger.info(f'bluetooth device {device_address} uuid is {uuid} start connecting...')
        # 基于MAC地址查找设备
        device = await BleakScanner.find_device_by_address(
            device_address, cb=dict(use_bdaddr=False)  # use_bdaddr判断是否是MOC系统
        )
        if device is None:
            logger.error("could not find device with address '%s'", device_address)
            info = 'false'
            view.page().runJavaScript("window.getConnectInfo('%s')" % info)
            return

        # 事件定义
        disconnected_event = asyncio.Event()

        # 断开连接事件回调，当设备断开连接时，会触发该函数，存在一定延迟
        def disconnected_callback(client):
            logger.error("Disconnected callback called!")
            # 蓝牙连接成功将信息返回给前端
            # 调用Js函数传参时必须要先声明变量再传参，直接传会报错
            info = 'false'
            view.page().runJavaScript("window.getConnectInfo('%s')" % info)
            disconnected_event.set()

        logger.info("connecting to device...")
        async with BleakClient(device, disconnected_callback=disconnected_callback) as client:
            logger.info("Connected")
            # list = client.get_services()
            list = client.services.services.values()
            for service in list:
                t_uuid = service.uuid
                characteristics = service.characteristics
                charList = []
                for characteristic in characteristics:
                    tempUuid = characteristic.uuid
                    tempDesc = characteristic.description
                    tempServiceUuid = characteristic.service_uuid
                    charList.append({'tempUuid': tempUuid, 'tempDesc': tempDesc, 'tempServiceUuid': tempServiceUuid})
                description = service.description
                logger.info('----> description: %s, uuid: %s, characteristics: %s' % (description, t_uuid, charList))

            await client.start_notify(uuid, notification_handler)
            # 蓝牙连接成功将信息返回给前端
            # 调用Js函数传参时必须要先声明变量再传参，直接传会报错
            info = 'true'
            view.page().runJavaScript("window.getConnectInfo('%s')" % info)

            # value1 = await client.read_gatt_char(uuid)
            # print('value',value)
            await disconnected_event.wait()  # 休眠直到设备断开连接，有延迟。此处为监听设备直到断开为止
            # await asyncio.sleep(10.0)           #程序监听的时间，此处为10秒
            # await client.stop_notify(par_notification_characteristic)


# https://blog.csdn.net/hp_cpp/article/details/83040162 强行停止python子线程最佳方案
def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)


# 开启另一个线程去启动web服务
class myServer(threading.Thread):
    def __init__(self, threadID, name, delay, port):
        logger.info(f"Starting myServer port:{port}")
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.delay = delay
        self.port = port

    def run(self):
        # myapp.main(self.port)
        fastApi.start(int(self.port))

    def terminate(self):
        pass


class myWebSocketServer(threading.Thread):
    def __init__(self, threadID, name, delay):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.delay = delay

    def run(self):
        # 启动websocket服务端
        MyWebsocketServer.main()


if __name__ == '__main__':
    cache = Cache('/cache')
    s = """                                                                                         
                                                                          
            |||      |||    ||||||||       ||||       ||||||||    |||||||||||||          
            |||      |||    ||||||||      ||||||      |||||||||   |||||||||||||          
            |||      |||    ||||||||      ||||||      ||||||||||  |||||||||||||          
            |||      |||    |||           ||||||      |||   ||||       |||               
            |||      |||    |||          ||||||||     |||    |||       |||               
            |||      |||    |||          |||  |||     |||    |||       |||               
            ||||||||||||    |||||||      |||  |||     |||   ||||       |||               
            ||||||||||||    |||||||     ||||  ||||    |||||||||        |||               
            ||||||||||||    |||||||     |||    |||    ||||||||         |||               
            |||      |||    |||         ||||||||||    ||||||||         |||               
            |||      |||    |||        ||||||||||||   |||  ||||        |||               
            |||      |||    |||        ||||||||||||   |||   ||||       |||               
            |||      |||    ||||||||   |||      |||   |||    |||       |||               
            |||      |||    ||||||||  ||||      ||||  |||    ||||      |||               
            |||      |||    ||||||||  |||       ||||  |||     ||||     |||               
            https://github.com/xiaoliu66/Heart                                                                
                                                                                      
    """
    logger.info(s)
    # 实例化缓存对象，指定缓存目录
    cache = Cache('/cache')
    cache.set('value', 0)
    cache.set('maxValue', 0)
    cache.set('minValue', 0)

    webSocketServer = MyWebsocketServer("localhost", 8000)
    webSocketServer.run()
    # 加载程序主窗口
    app = QApplication(sys.argv)
    view = WebEngine()

    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap("static/heart.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    app.setWindowIcon(icon)

    channel = QWebChannel()
    handler = CallHandler()  # 实例化QWebChannel的前端处理对象
    channel.registerObject('PyHandler', handler)  # 将前端处理对象在前端页面中注册为名PyHandler对象，此对象在前端访问时名称即为PyHandler'
    view.page().setWebChannel(channel)  # 挂载前端处理对象
    url_string = urllib.request.pathname2url(os.path.join(os.getcwd(), "./web/index.html"))  # 加载本地html文件
    view.load(QUrl(url_string))
    view.show()
    sys.exit(app.exec_())
