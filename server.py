import json
import logging
from functools import partial

import trio
from trio_websocket import serve_websocket, ConnectionClosed


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("trio-websocket").setLevel(logging.WARNING)

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


async def talk_to_browser(ws):
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


async def listen_browser(ws):
    while True:
        try:
            message = await ws.get_message()
            logger.debug(message)
        except ConnectionClosed:
            pass


async def connect_to_browser(request):
    ws = await request.accept()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(talk_to_browser, ws)
        nursery.start_soon(listen_browser, ws)


async def main():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(partial(serve_websocket, server, '127.0.0.1', 8080, ssl_context=None))
        nursery.start_soon(partial(serve_websocket, connect_to_browser, '127.0.0.1', 8000, ssl_context=None))


trio.run(main)
