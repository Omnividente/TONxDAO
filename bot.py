import sys
import threading
import time
import os
import socket
import requests
import keyboard
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import random

sys.dont_write_bytecode = True

from secretniy import base
from core.token import get_token, get_centrifugo_token
from core.info import get_info
from core.task import process_check_in, process_do_task
from core.ws import process_farm
from core.headers import headers


class TONxDAO:
    def __init__(self):
        # Get file directory
        self.data_file = base.file_path(file_name="data.txt")
        self.config_file = base.file_path(file_name="config.json")
        self.proxy_file = base.file_path(file_name="proxies.txt")
        self.user_agent_file = base.file_path(file_name="useragents.txt")

        # Initialize line
        self.line = base.create_line(length=50)

        # Get config
        self.auto_check_in = base.get_config(config_file=self.config_file, config_name="auto-check-in")
        self.auto_do_task = base.get_config(config_file=self.config_file, config_name="auto-do-task")
        self.auto_farm = base.get_config(config_file=self.config_file, config_name="auto-farm")

        # Load proxies
        self.proxies = self.load_proxies()
        self.connected_proxies = []
        self.account_info_results = []

        # Load user agents
        self.user_agents = self.load_user_agents()

    def load_proxies(self):
        if os.path.exists(self.proxy_file):
            try:
                with open(self.proxy_file, 'r') as f:
                    proxies = f.read().splitlines()
                    if not proxies:
                        base.log(f"{base.red}Proxy file is empty. Stopping script.")
                        sys.exit()
                    return proxies
            except Exception as e:
                base.log(f"{base.red}Error reading proxy file: {e}. Stopping script.")
                sys.exit()
        else:
            base.log(f"{base.yellow}Proxy file not found. Working without proxies.")
            return None

    def load_user_agents(self):
        if os.path.exists(self.user_agent_file):
            try:
                with open(self.user_agent_file, 'r') as f:
                    user_agents = f.read().splitlines()
                    if not user_agents:
                        base.log(f"{base.red}User agent file is empty. Stopping script.")
                        sys.exit()
                    return user_agents
            except Exception as e:
                base.log(f"{base.red}Error reading user agent file: {e}. Stopping script.")
                sys.exit()
        else:
            base.log(f"{base.yellow}User agent file not found. Stopping script.")
            sys.exit()

    def check_proxy_connection(self, proxy):
        try:
            proxy = proxy.strip()
            parts = proxy.split(':')
            if len(parts) != 4:
                raise ValueError(f"Invalid proxy format. Expected format is Login:Password:IP:Port, got: {proxy}")
        
            login, password, ip, port = [part.strip() for part in parts]
            formatted_proxy = f'http://{login}:{password}@{ip}:{port}'
            proxies = {"http": formatted_proxy, "https": formatted_proxy}
            response = requests.get("https://example.com", proxies=proxies, timeout=20)
            if response.status_code == 200:
                self.connected_proxies.append(proxies)
                return True
        except requests.exceptions.Timeout:
            base.log(f"{base.red}Proxy connection timed out: {proxy}")
        except requests.exceptions.RequestException as e:
            base.log(f"{base.red}Proxy connection failed: {proxy} - {e}")
        return False

    def connect_all_proxies(self):
        if self.proxies:
            base.log(f"{base.green}Checking proxy connections...")
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(self.check_proxy_connection, proxy) for proxy in self.proxies]
                for future in futures:
                    future.result()
            if not self.connected_proxies:
                base.log(f"{base.red}No valid proxies available. Stopping script.")
                sys.exit()
            base.log(f"{base.green}All proxy connections established. Ready to start.")

    def get_proxy_for_thread(self, index):
        if self.connected_proxies:
            if index < len(self.connected_proxies):
                proxy = self.connected_proxies[index]
                ip = proxy['http'].split('://')[-1].split('@')[-1].split(':')[0]
                return proxy
            else:
                base.log(f"{base.red}Not enough connected proxies for all threads. Stopping script.")
                sys.exit()
        return None

    def get_user_agent_for_thread(self, index):
        if index < len(self.user_agents):
            return self.user_agents[index]
        else:
            base.log(f"{base.red}Not enough user agents for all threads. Stopping script.")
            sys.exit()

    def process_account(self, account_data, account_number, num_acc, proxy=None, user_agent=None):
        if proxy:
            ip = proxy['http'].split('://')[-1].split('@')[-1].split(':')[0]
            base.log(f"{base.green}Account {account_number} connecting to IP: {base.white}{ip}")

        try:
            token = get_token(data=account_data)

            if token:
                dao_id, user_name, coins, energy, max_energy = get_info(token=token, proxies=proxy, headers=headers(token), user_agent=user_agent)
                time.sleep(2)
                base.log(
                    f"{base.blue}{user_name} {base.green} - Balance: {base.white}{coins:,} - {base.green}Energy: {base.white}{energy} - {base.green}Max Energy: {base.white}{max_energy}"
                )
                centrifugo_token = get_centrifugo_token(token=token)
                time.sleep(1)    
                if self.auto_farm:
                    process_farm(token=centrifugo_token, dao_id=dao_id, proxies=proxy, username=user_name)
                else:
                    base.log(f"{base.yellow}Auto Farm: {base.red}OFF")
                time.sleep(1)
                if self.auto_check_in:
                    process_check_in(token=token, proxies=proxy, username=user_name, headers=headers(token), user_agent=user_agent)
                else:
                    base.log(f"{base.yellow}Auto Check-in: {base.red}OFF")
                time.sleep(1)
                if self.auto_do_task:
                    process_do_task(token=token, proxies=proxy, username=user_name, headers=headers(token), user_agent=user_agent)
                else:
                    base.log(f"{base.yellow}Auto Do Task: {base.red}OFF")
                time.sleep(1)
                info = get_info(token=token, proxies=proxy, headers=headers(token), user_agent=user_agent)
                time.sleep(2)
                self.account_info_results.append((user_name, coins, energy, max_energy))
            else:
                base.log(f"{base.red}Token not found! Please get new query id")
        except KeyboardInterrupt:
            base.log(f"{base.red}Script interrupted by user. Exiting...")
            sys.exit()
        except Exception as e:
            base.log(f"{base.red}Error: {base.white}{e}")

    def get_next_schedule(self):
        current_time = datetime.now()
        intervals = [
            (current_time.replace(hour=6, minute=50, second=0, microsecond=0), current_time.replace(hour=7, minute=15, second=0, microsecond=0)),
            (current_time.replace(hour=15, minute=45, second=0, microsecond=0), current_time.replace(hour=16, minute=10, second=0, microsecond=0)),
            (current_time.replace(hour=0, minute=5, second=0, microsecond=0), current_time.replace(hour=0, minute=20, second=0, microsecond=0)),
        ]
        schedules = []
        for start, end in intervals:
            if start < current_time:
                start += timedelta(days=1)
                end += timedelta(days=1)
            random_time = start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))
            schedules.append(random_time)
        return min(schedules, key=lambda x: (x - current_time).total_seconds())

    def main(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        while True:
            try:
                current_time = datetime.now()
                next_schedule = self.get_next_schedule()
                wait_time = (next_schedule - current_time).total_seconds()
                
                base.log(f"{base.yellow}Next launch at {next_schedule.strftime('%Y-%m-%d %H:%M:%S')} (UTC+3)")
                while wait_time > 0:
                    if keyboard.is_pressed('ctrl+shift+s'):
                        base.log(f"{base.green}Forced start initiated by user.")
                        break
                    time.sleep(1)
                    wait_time -= 1

                self.connect_all_proxies()                
                data = open(self.data_file, "r").read().splitlines()
                num_acc = len(data)
                base.log(self.line)
                base.log(f"{base.green}Number of accounts: {base.white}{num_acc}")
                threads = []
                # Clear the account info results from the previous cycle
                os.system('cls' if os.name == 'nt' else 'clear')
                self.account_info_results.clear()
                for no, account_data in enumerate(data):
                    proxy = self.get_proxy_for_thread(no) if self.connected_proxies else None
                    user_agent = self.get_user_agent_for_thread(no)
                    thread = threading.Thread(target=self.process_account, args=(account_data, no + 1, num_acc, proxy, user_agent))
                    threads.append(thread)

                for thread in threads:
                    thread.start()

                for thread in threads:
                    thread.join()

                # Print results of get_info for all accounts
                base.log(self.line)
                base.log(f"{base.green}Account information summary:")
                time.sleep(2)
                print(f"\033[36m{'Username':<20}\033[36m{'Coins':<10}\033[36m{'Energy':<10}\033[36m{'Max Energy':<10}")
                print("-" * 50)
                for user_name, coins, energy, max_energy in sorted(self.account_info_results, key=lambda x: x[1], reverse=True):
                    print(f"\033[36m{user_name:<20}\033[37m{coins:<10}\033[37m{energy:<10}\033[37m{max_energy:<10}")
                base.log(self.line)
            except KeyboardInterrupt:
                base.log(f"{base.red}Script interrupted by user. Exiting...")
                sys.exit()

if __name__ == "__main__":
    try:
        txd = TONxDAO()
        txd.main()
    except KeyboardInterrupt:
        sys.exit()
