# Автобусы на карте Москвы

Веб-приложение показывает передвижение автобусов на карте Москвы.

<img src="screenshots/buses.gif">

## Как запустить

### Карта
- Скачайте код
- Откройте в браузере файл index.html

### Сервер
Сервер написан на python3, код был написан с использованием версии 3.10.
Установите зависимости с помощью команды
```bash
pip install -r requirements.txt
```
#### Запуск сервера
У сервера имеются аргументы командной строки:
```bash
usage: server.py [-h] [-b BUS_PORT] [-B BROWSER_PORT] [-v]

options:
  -h, --help            show this help message and exit
  -b BUS_PORT, --bus-port BUS_PORT
                        port for buses data
  -B BROWSER_PORT, --browser-port BROWSER_PORT
                        port to connect browser
  -v, --logging         On logging
```
Поэтому запуск может выглядеть вот так:
```bash
python3 server.py -b 8080 -B 8000 -v
```
#### Запуск эмулятора автобусов
Имеется эмаулятор движений автобусов, созданный для тесторивания.

Также имеются аргументы командной строки:
```bash
usage: fake_bus.py [-h] [-u URL] [-r ROUTES_NUMBER] [-b BUSES_PER_ROUTE]
                   [-w WEBSOCKET_NUMBER] [-e EMULATOR_ID] [-t REFRESH_TIMEOUT]
                   [-v LOGGING]

options:
  -h, --help            show this help message and exit
  -u URL, --url URL     url to send buses data
  -r ROUTES_NUMBER, --routes-number ROUTES_NUMBER
                        quantity of buses routes
  -b BUSES_PER_ROUTE, --buses-per-route BUSES_PER_ROUTE
                        quantity of buses per route
  -w WEBSOCKET_NUMBER, --websocket-number WEBSOCKET_NUMBER
                        quantity of opened websockets
  -e EMULATOR_ID, --emulator-id EMULATOR_ID
                        prefix to id of buses
  -t REFRESH_TIMEOUT, --refresh-timeout REFRESH_TIMEOUT
                        delay in updating coordinates
  -v LOGGING, --logging LOGGING
                        On logging
```
Поэтому запуск может выглядеть так:
```bash
python3 fake_bus.py -u ws://localhost:8080 -r 1000 -w 10 -e 13- -t 1 -v
```

#### Эмуляторы некорректных запросов
В репозитории также имеются эмуляторы некорректных запросов. Она нужны для тестирования валидации запросов.

Запускать их нужно только при включённом сервере командами:
```bash
python3 harmful_bus.py
python3 harmful_client.py
```
## Настройки

Внизу справа на странице можно включить отладочный режим логгирования и указать нестандартный адрес веб-сокета.

<img src="screenshots/settings.png">

Настройки сохраняются в Local Storage браузера и не пропадают после обновления страницы. Чтобы сбросить настройки удалите ключи из Local Storage с помощью Chrome Dev Tools —> Вкладка Application —> Local Storage.

Если что-то работает не так, как ожидалось, то начните с включения отладочного режима логгирования.

## Формат данных

Фронтенд ожидает получить от сервера JSON сообщение со списком автобусов:

```js
{
  "msgType": "Buses",
  "buses": [
    {"busId": "c790сс", "lat": 55.7500, "lng": 37.600, "route": "120"},
    {"busId": "a134aa", "lat": 55.7494, "lng": 37.621, "route": "670к"},
  ]
}
```

Те автобусы, что не попали в список `buses` последнего сообщения от сервера будут удалены с карты.

Фронтенд отслеживает перемещение пользователя по карте и отправляет на сервер новые координаты окна:

```js
{
  "msgType": "newBounds",
  "data": {
    "east_lng": 37.65563964843751,
    "north_lat": 55.77367652953477,
    "south_lat": 55.72628839374007,
    "west_lng": 37.54440307617188,
  },
}
```



## Используемые библиотеки

- [Leaflet](https://leafletjs.com/) — отрисовка карты
- [loglevel](https://www.npmjs.com/package/loglevel) для логгирования


## Цели проекта

Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org).
