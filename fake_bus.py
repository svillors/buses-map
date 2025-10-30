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


async def run_bus(url, bus_id, route):
    route_id = route.get('name')
    coords = route.get('coordinates')
    start = random.randrange(len(coords))
    lap = coords[start:] + coords[:start]
    try:
        async with open_websocket_url(url) as ws:
            for lat, lon in cycle(lap):
                await ws.send_message(json.dumps(
                    {
                        "busId": bus_id, "lat": lat,
                        "lng": lon, "route": route_id
                    }
                ))
                await trio.sleep(0.1)
    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)


async def main():
    url = 'ws://127.0.0.1:8080'
    routes = load_routes()
    limit = trio.Semaphore(200)

    async def create_one_bus(route):
        async with limit:
            await run_bus(url, generate_bus_id(route['name']), route)

    async def worker(route):
        async with trio.open_nursery() as nursery:
            for _ in range(random.randint(1, 4)):
                nursery.start_soon(create_one_bus, route)

    async with trio.open_nursery() as nursery:
        for route in routes:
            nursery.start_soon(worker, route)

trio.run(main)
