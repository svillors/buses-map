import json
import logging
import argparse
from dataclasses import dataclass, asdict
from functools import partial

import trio
from trio_websocket import serve_websocket, ConnectionClosed


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("trio-websocket").setLevel(logging.WARNING)

buses = {}


@dataclass
class Bus:
    busId: str
    lat: float
    lng: float
    route: str


@dataclass
class WindowBounds:
    south_lat: float
    north_lat: float
    west_lng: float
    east_lng: float

    def is_inside(self, lat, lng):
        return (
            self.south_lat <= lat <= self.north_lat
            and self.west_lng <= lng <= self.east_lng
        )

    def update(self, bounds):
        coords = bounds['data']
        self.south_lat = coords["south_lat"]
        self.north_lat = coords["north_lat"]
        self.west_lng = coords["west_lng"]
        self.east_lng = coords["east_lng"]


async def server(request):
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
            bus_info = json.loads(message)
            bus = Bus(**bus_info)
            buses[bus.busId] = bus
        except ConnectionClosed:
            break


async def send_buses(ws, bounds):
    visible_buses = [
        asdict(bus)
        for bus in buses.values()
        if bounds.is_inside(bus.lat, bus.lng)
    ]
    payload = json.dumps({
        "msgType": "Buses",
        "buses": visible_buses,
    })
    await ws.send_message(payload)


async def talk_to_browser(ws, window_bounds):
    while True:
        try:
            await send_buses(ws, window_bounds)
            await trio.sleep(1)
        except ConnectionClosed:
            break


async def listen_browser(ws, window_bounds):
    while True:
        try:
            message = await ws.get_message()
            logger.debug(message)
            window_bounds.update(json.loads(message))
        except ConnectionClosed:
            break


async def connect_to_browser(request):
    ws = await request.accept()
    window_bounds = WindowBounds(1, 1, 1, 1)
    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws, window_bounds)
        nursery.start_soon(talk_to_browser, ws, window_bounds)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-b', '--bus-port',
        help='port for buses data',
        type=int,
        default=8080
    )
    parser.add_argument(
        '-B', '--browser-port',
        help='port to connect browser',
        type=int,
        default=8000
    )
    parser.add_argument(
            '-v', '--logging',
            help='On logging'
    )
    args = parser.parse_args()

    async with trio.open_nursery() as nursery:
        nursery.start_soon(
            partial(
                serve_websocket, server,
                '127.0.0.1', args.bus_port,
                ssl_context=None
            )
        )
        nursery.start_soon(
            partial(
                serve_websocket, connect_to_browser,
                '127.0.0.1', args.browser_port,
                ssl_context=None
            )
        )

if __name__ == "__main__":
    trio.run(main)
