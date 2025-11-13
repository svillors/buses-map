import json
import logging
import argparse
from functools import partial
from typing import Literal

import trio
from trio_websocket import serve_websocket, ConnectionClosed
from pydantic import BaseModel, ValidationError


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("trio-websocket").setLevel(logging.WARNING)

buses = {}


class Bus(BaseModel):
    busId: str
    lat: float
    lng: float
    route: str


class WindowBounds(BaseModel):
    south_lat: float
    north_lat: float
    west_lng: float
    east_lng: float

    def is_inside(self, lat, lng):
        return (
            self.south_lat <= lat <= self.north_lat
            and self.west_lng <= lng <= self.east_lng
        )

    def update_from_bounds_msg(self, bounds_msg):
        for key, value in bounds_msg.data.model_dump().items():
            setattr(self, key, value)


class BoundsMessage(BaseModel):
    msgType: Literal["newBounds"]
    data: WindowBounds


async def server(logging, request):
    ws = await request.accept()
    if logging:
        logger.debug('Connected. Started colleting bus data')
    while True:
        try:
            message = await ws.get_message()
            try:
                bus = Bus.model_validate_json(message)
            except ValidationError as e:
                await ws.send_message(json.dumps({
                    "msgType": "Errors",
                    "errors": [f"{error['msg']}" for error in e.errors()]
                }))
                if logging:
                    logger.warning(f'Invalid response: {message}')
                continue
            buses[bus.busId] = bus
        except ConnectionClosed:
            if logging:
                logger.error('Connection closed to server')
            break


async def send_buses(ws, bounds):
    visible_buses = [
        bus.model_dump()
        for bus in buses.values()
        if bounds.is_inside(bus.lat, bus.lng)
    ]
    payload = json.dumps({
        "msgType": "Buses",
        "buses": visible_buses,
    })
    await ws.send_message(payload)


async def talk_to_browser(ws, window_bounds, logging):
    if logging:
        logger.debug('Connected. Started send data')
    while True:
        try:
            await send_buses(ws, window_bounds)
            await trio.sleep(1)
        except ConnectionClosed:
            if logging:
                logger.error('Connection closed to client')
            break


async def listen_browser(ws, window_bounds, logging):
    if logging:
        logger.debug('Connected. Started geting user map data')
    while True:
        try:
            message = await ws.get_message()
            try:
                bounds_message = BoundsMessage.model_validate_json(message)
            except ValidationError as e:
                await ws.send_message(json.dumps({
                    "msgType": "Errors",
                    "errors": [f"{error['msg']}" for error in e.errors()]
                }))
                if logging:
                    logger.warning(f'Invalid response: {message}')
                continue

            window_bounds.update_from_bounds_msg(bounds_message)
        except ConnectionClosed:
            if logging:
                logger.error('Connection closed to client')
            break


async def connect_to_browser(logging, request):
    ws = await request.accept()
    window_bounds = WindowBounds(
        north_lat=1, south_lat=1,
        east_lng=1, west_lng=1
    )
    async with trio.open_nursery() as nursery:
        nursery.start_soon(listen_browser, ws, window_bounds, logging)
        nursery.start_soon(talk_to_browser, ws, window_bounds, logging)


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
        help='On logging',
        action='store_true'
    )
    args = parser.parse_args()

    async with trio.open_nursery() as nursery:
        nursery.start_soon(
            partial(
                serve_websocket, partial(server, args.logging),
                '127.0.0.1', args.bus_port,
                ssl_context=None
            )
        )
        nursery.start_soon(
            partial(
                serve_websocket, partial(connect_to_browser, args.logging),
                '127.0.0.1', args.browser_port,
                ssl_context=None
            )
        )

if __name__ == "__main__":
    trio.run(main)
