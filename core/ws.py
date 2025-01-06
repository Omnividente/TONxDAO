import asyncio
import websockets
import sys
import json
import threading
import time
from secretniy import base
from queue import Queue
from websocket import WebSocketApp

sys.dont_write_bytecode = True


class WebSocketRequest:
    def __init__(self, proxy=None, headers=None):
        self.ws = None
        self.message_id = 1
        self.connected = False
        self.response_queue = Queue()
        self.dao_id = None
        self.proxy = proxy

    def connect_websocket(self, token, dao_id, proxy=None, headers=None):
        self.dao_id = dao_id
        self.token = token
        self.proxy = proxy
        ws_url = "wss://ws.production.tonxdao.app/ws"

        # Устанавливаем параметры прокси
        proxy_args = {}
        if proxy and proxy["protocol"] == "socks5":
            proxy_args = {
                "http_proxy_host": proxy["proxy_host"],
                "http_proxy_port": proxy["proxy_port"],
                "http_proxy_auth": proxy["proxy_auth"],
            }

        # Устанавливаем заголовки
        ws_headers = headers if headers else {
            "User-Agent": "MyCustomUserAgent/1.0",
            "Authorization": f"Bearer {self.token}"
        }

        self.ws = WebSocketApp(
            ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            # Преобразуем dict в список строк
            header=[f"{key}: {value}" for key, value in ws_headers.items()]
        )

        self.wst = threading.Thread(
            target=self.ws.run_forever,
            kwargs={
                "http_proxy_host": proxy_args.get("http_proxy_host"),
                "http_proxy_port": proxy_args.get("http_proxy_port"),
                "http_proxy_auth": proxy_args.get("http_proxy_auth"),
            } if proxy_args else {},
        )
        self.wst.daemon = True
        self.wst.start()

    def on_open(self, ws):
        self.connected = True
        self.send_message(
            {"connect": {"token": self.token, "name": "js"}, "id": self.message_id}
        )

    def on_message(self, ws, message):
        self.response_queue.put(message)

    def on_error(self, ws, error):
        base.log(f"{base.red}WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        self.connected = False

    def send_message(self, message):
        if not self.connected:
            return

        self.ws.send(json.dumps(message))
        self.message_id += 1

    def get_response(self, timeout=10):
        try:
            response = self.response_queue.get(timeout=timeout)
            return json.loads(response)
        except Queue.Empty:
            base.log(f"{base.yellow}No response received within timeout")
            return None

    def sync_request(self):
        self.send_message(
            {"rpc": {"method": "sync", "data": {}}, "id": self.message_id}
        )
        return self.get_response()

    def publish_request(self):
        self.send_message(
            {
                "publish": {"channel": f"dao:{self.dao_id}", "data": {}},
                "id": self.message_id,
            }
        )
        return self.get_response()


def process_farm(token, dao_id, proxies=None, username=None, headers=None, energy_threshold=5, max_retries=500):
    try:
        retry_count = 0
        while retry_count < max_retries:
            # Инициализация WebSocket с поддержкой прокси и заголовков
            ws_request = WebSocketRequest(proxy=proxies, headers=headers)
            ws_request.connect_websocket(token, dao_id)
            retry_count += 1

            # Ожидание установки соединения
            while not ws_request.connected:
                if retry_count >= max_retries:
                    base.log(
                        f"{base.red}Failed to connect after {max_retries} retries. Exiting..."
                    )
                    return
                time.sleep(0.1)

            connection_response = ws_request.get_response()

            energy = energy_threshold
            while ws_request.connected and energy >= energy_threshold:
                try:
                    # Отправляем запрос на ферму
                    publish_response = ws_request.publish_request()

                    # Получаем информацию
                    sync_response = ws_request.sync_request()

                    # Извлекаем данные
                    energy = sync_response["rpc"]["data"].get("energy", 0)

                    if energy < energy_threshold:
                        break
                except KeyboardInterrupt:
                    base.log(
                        f"{base.red}Script interrupted by user. Exiting..."
                    )
                    sys.exit()
                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        base.log(
                            f"{base.red}Max retries reached. Exiting..."
                        )
                        return
                    time.sleep(2)
                    break

                time.sleep(0.01)

            if energy < energy_threshold:
                base.log(
                    f"{base.blue}{username} {base.yellow}Energy is too low. Stop!"
                )
                break
    except KeyboardInterrupt:
        base.log(f"{base.red}Script interrupted by user. Exiting...")
        sys.exit()
