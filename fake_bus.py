import os
import json
import random
import string
import argparse
from itertools import cycle, islice
from sys import stderr

import trio
from trio_websocket import open_websocket_url


def generate_bus_id(route_id):
    alphabet = string.ascii_letters + string.digits
    bus_index = ''.join(random.choice(alphabet) for _ in range(5))
    return f"{route_id}-{bus_index}"


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


async def run_bus(url, bus_id, route, send_channel, delay):
    route_id = route.get('name')
    coords = route.get('coordinates')
    start = random.randrange(len(coords))
    lap = coords[start:] + coords[:start]
    try:
        async with send_channel:
            for lat, lon in cycle(lap):
                await send_channel.send(json.dumps(
                    {
                        "busId": bus_id, "lat": lat,
                        "lng": lon, "route": route_id
                    }
                ))
                await trio.sleep(delay)
    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)


async def send_updates(url, receive_channel):
    async with open_websocket_url(url) as ws, receive_channel:
        async for message in receive_channel:
            await ws.send_message(message)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-u', '--url',
        help='url to send buses data',
        type=str,
        default='ws://127.0.0.1:8080' # удалить
    )
    parser.add_argument(
        '-r', '--routes-number',
        help='quantity of buses routes',
        type=int,
        default=1000
    )
    parser.add_argument(
        '-b', '--buses-per-route',
        help='quantity of buses per route',
        type=int,
        default=10
    )
    parser.add_argument(
        '-w', '--websocket-number',
        help='quantity of opened websockets',
        type=int,
        default=10
    )
    parser.add_argument(
        '-e', '--emulator-id',
        help='prefix to id of buses',
        type=str,
        default=''
    )
    parser.add_argument(
        '-t', '--refresh-timeout',
        help='delay in updating coordinates',
        default=1
    )
    parser.add_argument(
        '-v', '--logging',
        help='On logging',
    )
    args = parser.parse_args()

    url = args.url
    routes = islice(load_routes(), args.routes_number)

    receive_channels = []
    send_channels = []

    async def create_one_bus(route, send_channel):
        await run_bus(
            url,
            args.emulator_id + generate_bus_id(route['name']),
            route,
            send_channel,
            args.refresh_timeout
        )

    async def worker(route, send_channel):
        async with trio.open_nursery() as nursery:
            for _ in range(args.buses_per_route):
                nursery.start_soon(create_one_bus, route, send_channel)

    for _ in range(args.websocket_number):
        send_channel, receive_channel = trio.open_memory_channel(1000)
        receive_channels.append(receive_channel)
        send_channels.append(send_channel)

    async with trio.open_nursery() as nursery:
        for receive_channel in receive_channels:
            nursery.start_soon(send_updates, url, receive_channel)

        for route in routes:
            nursery.start_soon(worker, route, random.choice(send_channels))


if __name__ == "__main__":
    trio.run(main)
