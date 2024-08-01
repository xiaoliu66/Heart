import sys
import os
import threading
import urllib.request
from datetime import time

from PyQt5 import QtWebEngineWidgets
from PyQt5.QtWidgets import QApplication, QDesktopWidget
from PyQt5.QtCore import QObject, pyqtSlot, QUrl, Qt, QPoint, QThread
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEnginePage
import json
import asyncio
from bleak import BleakScanner, BleakClient, BleakGATTCharacteristic

# 设备的Characteristic UUID
par_notification_characteristic = "00002a37-0000-1000-8000-00805f9b34fb"
# par_notification_characteristic = "0000180d-0000-1000-8000-00805f9b34fb"
# 设备的MAC地址
# device_address = "C8:06:E2:3C:E1:91"
device_address = ""


# 搜索蓝牙设备信息
async def searchBluetoothDevices():
    devices = await BleakScanner.discover()
    list = [];
    for d in devices:
        name = ''
        if (d.name is not None):
            name = d.name

        bluetooth_info = {"address": d.address, "name": name}
        print(bluetooth_info)
        list.append(bluetooth_info)
    print(list)
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

    print('❤:', value)
    view.page().runJavaScript("window.getHeartNum('%s')" % value)
    return value
    # print(data.decode('ascii'))
    # print(data)


class CallHandler(QObject):

    def __init__(self):
        super(CallHandler, self).__init__()

    # 搜索附件的蓝牙设备信息并返回给前端
    @pyqtSlot(str, result=str)  # 第一个参数即为回调时携带的参数类型
    def initSearch(self, str_args):
        print('------> initSearch......')
        print(str_args)  # 查看参数

        msg = asyncio.run(searchBluetoothDevices())
        # view.page().runJavaScript("alert('%s')" % msg)
        view.page().runJavaScript("window.initSearch('%s')" % msg)
        # info = '蓝牙设备连接成功！'
        # view.page().runJavaScript("window.get_info('%s')" % info)
        return 'hello, Python'

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
        print('bluetooth' + str_args + ' connecting......')
        print(str_args)  # 查看参数
        device_address = str_args
        print('thread %s is running...' % threading.current_thread().name)

        thread1 = myThread(1, "Thread-1", 0, device_address);
        thread1.start()
        # asyncio.run(self.startConnect(device_address))

    @pyqtSlot(result=int)
    def getHeartNum(self):
        print("getHeartNum:", value)
        view.page().runJavaScript("window.getHeartNum('%s')" % value)
        return value


class WebEngine(QWebEngineView):
    def __init__(self):
        super(WebEngine, self).__init__()
        self.setContextMenuPolicy(Qt.NoContextMenu)  # 设置右键菜单规则为自定义右键菜单
        # self.customContextMenuRequested.connect(self.showRightMenu)  # 这里加载并显示自定义右键菜单，我们重点不在这里略去了详细带吗
        self.setWindowTitle('QWebChannel与前端交互')
        self.resize(1200, 800)
        # cp = QDesktopWidget().availableGeometry().center()
        # self.move(QPoint(cp.x() - self.width() / 2, cp.y() - self.height() / 2))

# 开启另一个线程去连接蓝牙 实时获取心跳值
class myThread(threading.Thread):
    d_address = "";

    def __init__(self, threadID, name, delay, bluetoothAdresss):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.delay = delay
        self.d_address = bluetoothAdresss;

    def run(self):
        print('thread %s is running...' % threading.current_thread().name)
        asyncio.run(self.startConnect(self.d_address))

    async def startConnect(self, device_address):
        print('thread %s is running...' % threading.current_thread().name)
        print('bluetooth device %s start connecting...' % device_address)
        # 基于MAC地址查找设备
        device = await BleakScanner.find_device_by_address(
            device_address, cb=dict(use_bdaddr=False)  # use_bdaddr判断是否是MOC系统
        )
        if device is None:
            print("could not find device with address '%s'", device_address)
            return

        # 事件定义
        disconnected_event = asyncio.Event()

        # 断开连接事件回调，当设备断开连接时，会触发该函数，存在一定延迟
        def disconnected_callback(client):
            print("Disconnected callback called!")
            # 蓝牙连接成功将信息返回给前端
            # 调用Js函数传参时必须要先声明变量再传参，直接传会报错
            info = 'false'
            view.page().runJavaScript("window.getConnectInfo('%s')" % info)
            disconnected_event.set()

        print("connecting to device...")
        async with BleakClient(device, disconnected_callback=disconnected_callback) as client:
            print("Connected")
            # list = client.get_services()
            list = client.services.services.values()
            for service in list:
                uuid = service.uuid
                characteristics = service.characteristics
                charList = []
                for characteristic in characteristics:
                    tempUuid = characteristic.uuid
                    tempDesc = characteristic.description
                    tempServiceUuid = characteristic.service_uuid
                    charList.append({'tempUuid': tempUuid, 'tempDesc': tempDesc, 'tempServiceUuid': tempServiceUuid})
                description = service.description
                print('----> description: %s, uuid: %s, characteristics: %s' % (description, uuid, charList))

            await client.start_notify(par_notification_characteristic, notification_handler)
            # 蓝牙连接成功将信息返回给前端
            # 调用Js函数传参时必须要先声明变量再传参，直接传会报错
            info = 'true'
            view.page().runJavaScript("window.getConnectInfo('%s')" % info)

            # value1 = await client.read_gatt_char(uuid)
            # print('value',value)
            await disconnected_event.wait()  # 休眠直到设备断开连接，有延迟。此处为监听设备直到断开为止
            # await asyncio.sleep(10.0)           #程序监听的时间，此处为10秒
            # await client.stop_notify(par_notification_characteristic)


if __name__ == '__main__':
    # 加载程序主窗口
    app = QApplication(sys.argv)
    view = WebEngine()

    channel = QWebChannel()
    handler = CallHandler()  # 实例化QWebChannel的前端处理对象
    channel.registerObject('PyHandler', handler)  # 将前端处理对象在前端页面中注册为名PyHandler对象，此对象在前端访问时名称即为PyHandler'
    view.page().setWebChannel(channel)  # 挂载前端处理对象
    url_string = urllib.request.pathname2url(os.path.join(os.getcwd(), "index.html"))  # 加载本地html文件
    view.load(QUrl(url_string))
    view.show()
    sys.exit(app.exec_())
