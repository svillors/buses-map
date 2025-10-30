import os
import trio
import json
from sys import stderr
from trio_websocket import open_websocket_url


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)


async def run_bus(url, route):
    bus_id = route.get('name')
    coords = route.get('coordinates')
    try:
        async with open_websocket_url(url) as ws:
            for lat, lon in coords:
                await ws.send_message(json.dumps(
                    {
                        "busId": bus_id, "lat": lat,
                        "lng": lon, "route": bus_id
                    }
                ))
                await trio.sleep(1)
    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)


async def main():
    url = 'ws://127.0.0.1:8080'
    routes = load_routes()
    limit = trio.Semaphore(100)

    async def worker(route):
        async with limit:
            await run_bus(url, route)

    async with trio.open_nursery() as nursery:
        async with limit:
            for route in routes:
                nursery.start_soon(worker, route)

trio.run(main)
