import trio
import json
from sys import stderr
from trio_websocket import open_websocket_url


async def main():
    with open('bus.json', encoding='utf-8') as f:
        bus = json.load(f)
    try:
        async with open_websocket_url('ws://127.0.0.1:8080') as ws:
            for lat, lon in bus['coordinates']:
                await ws.send_message(json.dumps(
                    {
                        "busId": bus['name'], "lat": lat,
                        "lng": lon, "route": bus['name']
                    }
                ))
                await trio.sleep(1)
    except OSError as ose:
        print('Connection attempt failed: %s' % ose, file=stderr)

trio.run(main)