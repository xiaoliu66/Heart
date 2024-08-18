import asyncio
import json
import logging
import os
import threading
import time

import websockets
from diskcache import Cache
from loguru import logger

global myWebsocket

cache = Cache('/cache')


class MyWebsocketServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def echo(self, websocket):
        logger.info("------ Echoing WebSocket --------")
        async for message in websocket:
            logger.info(message)
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
        logger.info("======== websocket server is start ... ========")
        asyncio.set_event_loop(asyncio.new_event_loop())
        start_server = websockets.serve(self.echo, self.host, self.port)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
        logger.info("连接成功！")

    def run(self):
        t = threading.Thread(target=self.connect)
        t.start()

    def stopServer(self):
        os._exit(0)
