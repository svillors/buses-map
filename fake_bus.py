import os
import json
import random
import string
from itertools import cycle
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


async def run_bus(url, bus_id, route, send_channel):
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
                await trio.sleep(0.1)
    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)


async def send_updates(url, receive_channel):
    async with open_websocket_url(url) as ws, receive_channel:
        async for message in receive_channel:
            await ws.send_message(message)


async def main():
    url = 'ws://127.0.0.1:8080'
    routes = load_routes()
    limit = trio.Semaphore(20000)

    receive_channels = []
    send_channels = []

    async def create_one_bus(route, send_channel):
        async with limit:
            await run_bus(url, generate_bus_id(route['name']), route, send_channel)

    async def worker(route, send_channel):
        async with trio.open_nursery() as nursery:
            for _ in range(random.randint(27, 33)):
                nursery.start_soon(create_one_bus, route, send_channel)

    for _ in range(10):
        send_channel, receive_channel = trio.open_memory_channel(500)
        receive_channels.append(receive_channel)
        send_channels.append(send_channel)

    async with trio.open_nursery() as nursery:
        for receive_channel in receive_channels:
            nursery.start_soon(send_updates, url, receive_channel)

        for route in routes:
            nursery.start_soon(worker, route, random.choice(send_channels))


if __name__ == "__main__":
    trio.run(main)
