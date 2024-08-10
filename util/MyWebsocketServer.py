import asyncio
import json
import threading
import time

import websockets
from diskcache import Cache

global myWebsocket


cache = Cache('/cache')
class MyWebsocketServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def echo(self, websocket):
        print("------ Echoing WebSocket --------")
        async for message in websocket:
            print(message)
            # await websocket.send("Received: " + message)

            while True:
                value = cache.get("value")
                maxValue = cache.get('maxValue')
                minValue = cache.get('minValue')

                heartInfo = {"value": value, "maxValue": maxValue, "minValue": minValue}
                # print(heartInfo)
                await websocket.send(json.dumps(heartInfo))
                await asyncio.sleep(0.5)




    def connect(self):
        print("======== websocket server is start ... ========")
        asyncio.set_event_loop(asyncio.new_event_loop())
        start_server = websockets.serve(self.echo, self.host, self.port)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
        print("连接成功！")


    def run(self):
        t = threading.Thread(target=self.connect)
        t.start()
