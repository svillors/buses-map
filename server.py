import json
import logging
from functools import partial

import trio
from trio_websocket import serve_websocket, ConnectionClosed


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("trio-websocket").setLevel(logging.WARNING)

buses = {}


def is_inside(bounds, lat, lng):
    coords = bounds['data']
    return (
        (coords['south_lat'] <= lat <= coords['north_lat'])
        and (coords['west_lng'] <= lng <= coords['east_lng'])
    )


async def server(request):
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
            bus_info = json.loads(message)
            buses[bus_info['busId']] = bus_info
        except ConnectionClosed:
            break


async def send_buses(ws, bounds):
    visible_buses = [
        bus for bus in buses.values()
        if is_inside(bounds, bus['lat'], bus['lng'])
    ]
    payload = json.dumps({
        "msgType": "Buses",
        "buses": visible_buses,
    })
    await ws.send_message(payload)


async def listen_browser(ws):
    while True:
        try:
            message = await ws.get_message()
            logger.debug(message)
            bounds = json.loads(message)
            await send_buses(ws, bounds)
        except ConnectionClosed:
            pass


async def connect_to_browser(request):
    ws = await request.accept()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws)


async def main():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(partial(serve_websocket, server, '127.0.0.1', 8080, ssl_context=None))
        nursery.start_soon(partial(serve_websocket, connect_to_browser, '127.0.0.1', 8000, ssl_context=None))


trio.run(main)
