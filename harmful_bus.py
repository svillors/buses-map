import json
from itertools import cycle

import trio
from trio_websocket import open_websocket_url


CASES = [
    'qwe',
    {"busId": '123', "lat": 'qwe', "lng": 'qwe', "route": '123'},
    {"lat": 1, "lng": 1, "route": '123'},
    {}
]


async def get_responses(ws):
    while True:
        response = await ws.get_message()
        data = json.loads(response)
        if data.get("msgType") == "Errors":
            print(f"Response: {data}")


async def send_cases(ws):
    for case in cycle(CASES):
        await ws.send_message(json.dumps(case))
        await trio.sleep(1)


async def main():
    async with open_websocket_url("ws://127.0.0.1:8080") as ws:
        async with trio.open_nursery() as nursery:
            nursery.start_soon(send_cases, ws)
            nursery.start_soon(get_responses, ws)


if __name__ == "__main__":
    trio.run(main)
