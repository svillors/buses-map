import json
from functools import partial

import trio
from trio_websocket import serve_websocket, ConnectionClosed


buses = {}


async def server(request):
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
            bus_info = json.loads(message)
            buses[bus_info['busId']] = bus_info
        except ConnectionClosed:
            break


async def talk_to_browser(request):
    ws = await request.accept()
    while True:
        try:
            buses_info = list(buses.values())
            payload = json.dumps({
                "msgType": "Buses",
                "buses": buses_info
            })
            await ws.send_message(payload)
            await trio.sleep(1)
        except ConnectionClosed:
            break


async def main():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(partial(serve_websocket, server, '127.0.0.1', 8080, ssl_context=None))
        nursery.start_soon(partial(serve_websocket, talk_to_browser, '127.0.0.1', 8000, ssl_context=None))


trio.run(main)
