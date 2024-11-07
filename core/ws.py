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
    def __init__(self):
        self.ws = None
        self.message_id = 1
        self.connected = False
        self.response_queue = Queue()
        self.dao_id = None

    def connect_websocket(self, token, dao_id):
        self.dao_id = dao_id
        self.token = token
        ws_url = "wss://ws.production.tonxdao.app/ws"
        self.ws = WebSocketApp(
            ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        self.wst = threading.Thread(target=self.ws.run_forever)
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


def process_farm(token, dao_id, proxies=None, username=None, headers=None, user_agent=None, energy_threshold=5, max_retries=500):
    try:
        retry_count = 0
        while retry_count < max_retries:
            ws_request = WebSocketRequest()
            ws_request.connect_websocket(token, dao_id)
            retry_count += 1

            # Wait for the connection to be established
            while not ws_request.connected:
                if retry_count >= max_retries:
                    base.log(f"{base.red}Failed to connect after {max_retries} retries. Exiting...")
                    return
                time.sleep(0.1)

            connection_response = ws_request.get_response()

            energy = energy_threshold
            while ws_request.connected and energy >= energy_threshold:
                try:
                    # Send farm request
                    publish_response = ws_request.publish_request()

                    # Get info
                    sync_response = ws_request.sync_request()

                    coins = sync_response["rpc"]["data"]["coins"]
                    dao_coins = sync_response["rpc"]["data"]["dao_coins"]
                    energy = sync_response["rpc"]["data"]["energy"]              
                    #base.log(f"{base.blue}{username} {base.green}Coins: {base.white}{coins:,} - {base.green}DAO Coins: {base.white}{dao_coins:,} - {base.green}Energy: {base.white}{energy}")

                    if energy < energy_threshold:
                        break
                except KeyboardInterrupt:
                    base.log(f"{base.red}Script interrupted by user. Exiting...")
                    sys.exit()
                except Exception as e:
                    #base.log(f"{base.red}Unexpected error: {e}. Retrying...")
                    retry_count += 1
                    retry_count += 1
                    if retry_count >= max_retries:
                        #base.log(f"{base.red}Max retries reached. Exiting...")
                        return
                    time.sleep(2)
                    break

                time.sleep(0.01)

            if energy < energy_threshold:
                base.log(f"{base.blue}{username} {base.yellow}Energy is too low. Stop!")
                break
    except KeyboardInterrupt:
        base.log(f"{base.red}Script interrupted by user. Exiting...")
        sys.exit()
