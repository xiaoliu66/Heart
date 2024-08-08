import asyncio
import websockets


async def server(websocket, path):
    async for message in websocket:
        print(message)
        await websocket.send("Received: " + message)


start_server = websockets.serve(server, "localhost", 8765)


def main():
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    event_loop.run_until_complete(start_server)
    event_loop.run_forever()
    # asyncio.get_event_loop().run_until_complete(start_server)
    # asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    print("======== websocket server is start ... ========")
    main()
