import json
from itertools import cycle

import trio
from trio_websocket import open_websocket_url


CASES = [
    {"msgType":"newBounds","data":{"south_lat":55.72943006127542,"north_lat":55.770586703857326,"west_lng":37.54165649414063,"east_lng":37.65830039978028}},
    {"msgType":"qweqwe","data":{"south_lat":55.72943006127542,"north_lat":55.770586703857326,"west_lng":37.54165649414063,"east_lng":37.65830039978028}},
    {"msgType":"newBounds","data":{"south_lat":55.72943006127542,"north_lat":55.770586703857326,"west_lng":37.54165649414063,"east_lng":37.65830039978028}},
    'qwe',
    {"msgType":"newBounds","data":{"north_lat":'qweqwe',"west_lng":37.54165649414063,"east_lng":37.65830039978028}},
    {"msgType":"newBounds","data":'qweqwe'},
    {"data":'qweqwe'}
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
    async with open_websocket_url("ws://127.0.0.1:8000") as ws:
        async with trio.open_nursery() as nursery:
            nursery.start_soon(send_cases, ws)
            nursery.start_soon(get_responses, ws)


if __name__ == "__main__":
    trio.run(main)
