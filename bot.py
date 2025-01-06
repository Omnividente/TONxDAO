from core.headers import get_headers
from core.ws import process_farm
from core.task import process_check_in, process_do_task
from core.info import get_info
from core.token import get_token, get_centrifugo_token
from concurrent.futures import ThreadPoolExecutor, as_completed
from secretniy import base
import sys
import threading
import time
import json
import pytz
import os
import socket
import socks
import requests
import keyboard
from concurrent.futures import ThreadPoolExecutor
from tzlocal import get_localzone
from datetime import datetime, timedelta
import random
from collections import defaultdict

sys.dont_write_bytecode = True


class TONxDAO:
    def __init__(self):
        # Get file directory
        self.data_file = base.file_path(file_name="data.txt")
        self.config_file = base.file_path(file_name="config.json")
        self.proxy_file = base.file_path(file_name="proxies.txt")
        self.grouped_dao = defaultdict(list)

        # Initialize line
        self.line = base.create_line(length=50)

        # Get config
        self.auto_check_in = base.get_config(
            config_file=self.config_file, config_name="auto-check-in")
        self.auto_do_task = base.get_config(
            config_file=self.config_file, config_name="auto-do-task")
        self.auto_farm = base.get_config(
            config_file=self.config_file, config_name="auto-farm")
        self.header_printed = False
        self.header_farming_printed = False
        self.create_new_accoint_json = False

        # Load proxies
        self.proxies = self.load_proxies()
        self.connected_proxies = []
        self.account_info_results = []
        self.original_socket = socket.socket

    def load_proxies(self):
        if os.path.exists(self.proxy_file):
            try:
                with open(self.proxy_file, 'r') as f:
                    proxies = f.read().splitlines()
                    if not proxies:
                        base.log(
                            f"{base.red}Proxy file is empty. Stopping script.")
                        sys.exit()

                    # Парсим каждую строку прокси
                    parsed_proxies = []
                    for proxy_str in proxies:
                        try:
                            parsed_proxy = self.parse_proxy(proxy_str)
                            parsed_proxies.append(parsed_proxy)
                        except ValueError as e:
                            base.log(f"{base.red}{e}")

                    if not parsed_proxies:
                        base.log(
                            f"{base.red}No valid proxies available. Stopping script.")
                        sys.exit()

                    return parsed_proxies
            except Exception as e:
                base.log(
                    f"{base.red}Error reading proxy file: {e}. Stopping script.")
                sys.exit()
        else:
            base.log(
                f"{base.yellow}Proxy file not found. Working without proxies.")
            return None

    def parse_proxy(self, proxy_str):
        try:
            protocol, rest = proxy_str.split("://")
            auth, host_and_port = rest.split("@")
            host, port = host_and_port.split(":")
            login, password = auth.split(":")
            if protocol.lower() not in ["http", "socks5"]:
                raise ValueError(f"Unsupported proxy protocol: {protocol}")
            return {
                "protocol": protocol.lower(),
                "proxy_host": host,
                "proxy_port": int(port),
                "proxy_auth": (login, password)
            }
        except Exception as e:
            raise ValueError(f"Error parsing proxy: {proxy_str}. Details: {e}")

    def configure_socks_proxy(self, proxy):
        """Настройка SOCKS5-прокси для сокетов"""
        if proxy["protocol"] == "socks5":
            socks.set_default_proxy(
                socks.SOCKS5,
                proxy["proxy_host"],
                proxy["proxy_port"],
                username=proxy["proxy_auth"][0],
                password=proxy["proxy_auth"][1]
            )
            socket.socket = socks.socksocket

    def reset_socks_proxy(self):
        """Сброс настроек прокси"""
        socket.socket = self.original_socket

    def get_mega_farm_time(syndicate_id, token, proxy=None, headers=None):
        """
        Получение значения `mega_farm_time` для синдиката.

        Args:
            syndicate_id (str): ID синдиката.
            token (str): Токен для аутентификации.
            proxy (dict, optional): Прокси-сервер в формате словаря.
            headers (dict, optional): Заголовки для запроса.

        Returns:
            int: Значение `mega_farm_time`, если успешно.
            None: Если произошла ошибка.
        """
        url = f"https://app.production.tonxdao.app/api/v1/syndicates/{syndicate_id}"

        try:
            # Устанавливаем заголовки
            if not headers:
                headers = get_headers(token=token)

            # Выполняем GET-запрос
            response = requests.get(
                url, headers=headers, proxies=proxy, timeout=20)
            response.raise_for_status()  # Проверяем HTTP статус

            # Парсим JSON ответ
            data = response.json()
            mega_farm_time = data.get("mega_farm_time")

            if mega_farm_time is not None:
                base.log(f"{base.green}Mega Farm Time: {mega_farm_time}")
                return mega_farm_time
            else:
                base.log(
                    f"{base.red}Mega Farm Time not found in response: {data}")
                return None
        except requests.exceptions.RequestException as req_err:
            base.log(f"{base.red}HTTP Request error: {req_err}")
        except Exception as e:
            base.log(f"{base.red}Unexpected error in get_mega_farm_time: {e}")

        return None

    def check_proxy_connection(self, proxy):
        try:
            if proxy["protocol"] == "socks5":
                self.configure_socks_proxy(proxy)

            response = requests.get(
                "https://example.com", timeout=10)  # Тайм-аут 10 секунд
            if response.status_code == 200:
                self.connected_proxies.append(proxy)
                return True
            else:
                base.log(
                    f"{base.red}Proxy {proxy} returned status code {response.status_code}.")
        except requests.exceptions.Timeout:
            base.log(f"{base.red}Proxy connection timed out: {proxy}")
        except requests.exceptions.RequestException as e:
            base.log(f"{base.red}Proxy connection failed: {proxy} - {e}")
        finally:
            self.reset_socks_proxy()  # Сбрасываем прокси для следующих запросов
        return False

    def connect_all_proxies(self):
        if self.proxies:
            base.log(f"{base.green}Checking proxy connections...")
            # Ограничиваем число потоков
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(self.check_proxy_connection, proxy): proxy
                    for proxy in self.proxies
                }
                # Обрабатываем потоки по мере завершения
                for future in as_completed(futures):
                    proxy = futures[future]
                    try:
                        # Устанавливаем тайм-аут для каждого задания
                        result = future.result(timeout=15)
                        # if result:
                        #     base.log(f"{base.green}Proxy {proxy} is valid.")
                        # else:
                        #     base.log(f"{base.red}Proxy {proxy} failed.")
                    except Exception as e:
                        base.log(
                            f"{base.red}Error checking proxy {proxy}: {e}")

            if not self.connected_proxies:
                base.log(
                    f"{base.red}No valid proxies available. Stopping script.")
                sys.exit()

            base.log(
                f"{base.green}All proxy connections established. Ready to start.")

    def get_proxy_for_thread(self, index):
        if self.connected_proxies:
            if index < len(self.connected_proxies):
                proxy = self.connected_proxies[index]
                base.log(
                    f"{base.green}Proxy assigned to thread {index}: {proxy}")
                return proxy
            else:
                base.log(
                    f"{base.red}Not enough connected proxies for thread {index}. No proxy assigned.")
                return None
        else:
            base.log(f"{base.red}No connected proxies available.")
            return None

    def process_account(self, account_data, proxy=None, headers=None):
        if proxy and proxy["protocol"] == "socks5":
            self.configure_socks_proxy(proxy)

        try:
            token = get_token(data=account_data, proxy=proxy, headers=headers)

            if token:
                # Получаем информацию об аккаунте
                info = get_info(token=token, proxies=proxy, headers=headers)
                if info:  # Проверяем, что данные успешно получены
                    dao_id, user_name, coins, energy, max_energy = info  # Распаковываем данные
                    # Логируем результат в структурированном формате

                    if not self.header_printed:
                        base.log("-" * 60)
                        base.log(
                            f"\033[36m{'DAO ID':<10}\033[36m{'Username':<20}\033[36m{'Coins':<10}\033[36m{'Energy':<10}\033[36m{'Max Energy':<10}"
                        )
                        base.log("-" * 60)
                        self.header_printed = True  # Устанавливаем флаг
                    base.log(
                        f"\033[36m{dao_id:<10}\033[36m{user_name:<20}\033[37m{coins:<10}\033[37m{energy:<10}\033[37m{max_energy:<10}"
                    )

                    # Получаем centrifugo_token
                    centrifugo_token = get_centrifugo_token(
                        token=token, proxy=proxy, headers=headers)

                    # # Выполняем автоматический фарм, если включено
                    if self.auto_farm:
                        if not self.header_farming_printed:
                            base.log("-" * 60)
                            base.log(f"{base.green}Launching farming ...")
                            self.header_farming_printed = True
                        process_farm(token=centrifugo_token, dao_id=dao_id,
                                     proxies=proxy, username=user_name)
                    else:
                        base.log(f"{base.yellow}Auto Farm: {base.red}OFF")

                    # Выполняем check-in, если включено
                    if self.auto_check_in:
                        process_check_in(
                            token=token, proxies=proxy, username=user_name, headers=headers)
                    else:
                        base.log(f"{base.yellow}Auto Check-in: {base.red}OFF")

                    # Выполняем задачи, если включено
                    if self.auto_do_task:
                        process_do_task(token=token, proxies=proxy,
                                        username=user_name, headers=headers)
                    else:
                        base.log(f"{base.yellow}Auto Do Task: {base.red}OFF")

                    # Повторно получаем данные аккаунта
                    updated_info = get_info(
                        token=token, proxies=proxy, headers=headers)
                    if updated_info:
                        dao_id, user_name, coins, energy, max_energy = updated_info

                    # Сохраняем финальные данные
                    self.account_info_results.append({
                        "user_name": user_name,
                        "coins": coins,
                        "energy": energy,
                        "max_energy": max_energy
                    })
                else:
                    base.log(f"{base.red}Failed to fetch account info.")
            else:
                base.log(f"{base.red}Token not found! Please get new query id")
        except KeyboardInterrupt:
            base.log(f"{base.red}Script interrupted by user. Exiting...")
            sys.exit()
        except Exception as e:
            base.log(f"{base.red}Error: {base.white}{e}")
        finally:
            # Сбрасываем SOCKS-прокси после использования
            if proxy and proxy["protocol"] == "socks5":
                socks.set_default_proxy(None)
                socket.socket = self.original_socket

    def create_new_dao(self, account_data=None, headers=None, proxies=None):
        url = "https://app.production.tonxdao.app/api/v1/dao"
        token = get_token(data=account_data, proxy=proxies, headers=headers)

        if token:
            if headers is None:
                headers = {}
            headers["Authorization"] = f"Bearer {token}"
            headers["Referer"] = "https://app.production.tonxdao.app/syndicates"
        try:
            response = requests.get(url, headers=headers, proxies=proxies)
            response.raise_for_status()  # Генерирует исключение для HTTP ошибок
            data = response.json()
            return data.get("id"), data.get("syndicate_id")
        except requests.exceptions.RequestException as e:
            self.log(f"Failed to get DAO information: {e}")
        return None, None

    def get_current_dao(self, headers, proxies):
        url = "https://app.production.tonxdao.app/api/v1/dao"
        try:
            response = requests.get(url, headers=headers, proxies=proxies)
            response.raise_for_status()  # Генерирует исключение для HTTP ошибок
            data = response.json()
            return data.get("id"), data.get("syndicate_id")
        except requests.exceptions.RequestException as e:
            self.log(f"Failed to get DAO information: {e}")
        return None, None

    def get_syndicate_info(self, syndicate_id, headers, proxies):
        url = f"https://app.production.tonxdao.app/api/v1/syndicates/{syndicate_id}"
        try:
            response = requests.get(url, headers=headers, proxies=proxies)
            response.raise_for_status()  # Генерирует исключение для HTTP ошибок
            return response.json()
        except requests.exceptions.RequestException as e:
            self.log(f"Failed to fetch syndicate info: {e}")
        return None

    def group_dao_and_get_syndicate_info(self, headers, proxies):
        # Получаем текущие DAO и синдикат
        dao_id, syndicate_id = self.get_current_dao(
            headers=headers, proxies=proxies)
        if not dao_id or not syndicate_id:
            self.log("Failed to retrieve DAO or Syndicate ID.")
            return

        # Если DAO уже обработан, пропускаем
        if dao_id in self.grouped_dao:
            return

        # Получаем информацию о синдикате
        syndicate_info = self.get_syndicate_info(
            syndicate_id, headers=headers, proxies=proxies)
        if not syndicate_info:
            self.log(f"Failed to fetch syndicate info for DAO ID {dao_id}.")
            return

        # Добавляем данные в grouped_dao
        self.grouped_dao[dao_id] = syndicate_info

    def group_all_dao_and_syndicates(self, accounts_data):
        """Собирает и группирует все данные о DAO и синдикатах."""
        for account_key, account_info in accounts_data.items():
            account_headers = account_info.get("headers")
            account_proxy = account_info.get("proxy")

            if not account_headers or not account_proxy:
                self.log(
                    f"Skipping account {account_key}: Missing headers or proxy.")
                continue

            # Группировка DAO и получение синдикатов
            self.group_dao_and_get_syndicate_info(
                headers=account_headers, proxies=account_proxy)

        # Вывод информации о синдикатах после группировки
        self.log("Grouped DAO and syndicate information:")
        for dao_id, syndicate_info in self.grouped_dao.items():
            self.log(
                f"DAO ID: {dao_id}, Syndicate ID: {syndicate_info['id']}, "
                f"Name: {syndicate_info['name']}, Mega Farm Time: {syndicate_info['mega_farm_time']}"
            )

    def log_grouped_data(self):
        self.log("Final grouped DAO information:")
        for dao_id, syndicate in self.grouped_dao.items():
            self.log(f"DAO ID: {dao_id}")
            self.log(
                f"  - Syndicate ID: {syndicate['id']}, Name: {syndicate['name']}, "
                f"Mega Farm Time: {syndicate['mega_farm_time']}, Members: {syndicate['members']}, Rank: {syndicate['rank']}"
            )

    def calculate_first_launch_time_auto(self, mega_farm_time_utc):
        """Вычисляет время первого запуска автоматически."""
        # Время мегафарма в UTC
        mega_farm_time_utc = datetime.strptime(mega_farm_time_utc, "%H:%M").replace(
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day,
            tzinfo=pytz.UTC
        )

        # Получение локального часового пояса
        local_timezone = get_localzone()
        mega_farm_time_local = mega_farm_time_utc.astimezone(local_timezone)

        # Диапазон времени для первого запуска
        start_time = mega_farm_time_local
        end_time = mega_farm_time_local + timedelta(minutes=25)

        # Случайное время внутри диапазона
        random_time = start_time + timedelta(
            seconds=random.randint(
                0, int((end_time - start_time).total_seconds()))
        )

        return random_time

    def get_account_dao_id(self, account_data):
        """
        Возвращает DAO ID, связанную с данным аккаунтом.
        """
        try:
            # Проверяем, что данные не пустые
            if not account_data.strip():
                self.log("Empty account data received. Skipping...")
                return None

            # Попробуем распарсить как JSON
            # Если account_data в формате JSON-строки
            account_info = json.loads(account_data)
            dao_id = account_info.get("dao_id")

            if dao_id:
                return dao_id
            else:
                self.log(f"DAO ID not found for account: {account_data}")
                return None
        except json.JSONDecodeError as e:
            self.log(
                f"Invalid JSON format for account data: {account_data}. Error: {e}")
            return None
        except Exception as e:
            self.log(
                f"Unexpected error while extracting DAO ID from account data: {e}")
            return None

    def get_dao_schedules(self, specific_dao_id=None):
        """Генерирует расписания для всех DAO или для конкретного DAO."""
        dao_schedules = {}
        target_dao_ids = [
            specific_dao_id] if specific_dao_id else self.grouped_dao.keys()

        current_time = datetime.now(get_localzone())

        for dao_id in target_dao_ids:
            syndicate_info = self.grouped_dao.get(dao_id)
            if not syndicate_info:
                continue

            mega_farm_time_utc = syndicate_info.get("mega_farm_time")
            if not mega_farm_time_utc:
                self.log(
                    f"Skipping DAO ID {dao_id}: Mega Farm Time not available.")
                continue

            schedules = []

            # Время мегафарма (UTC)
            mega_farm_time_utc = datetime.strptime(mega_farm_time_utc, "%H:%M").replace(
                year=datetime.now().year,
                month=datetime.now().month,
                day=datetime.now().day,
                tzinfo=pytz.UTC
            )

            # Получение локального часового пояса
            local_timezone = get_localzone()
            mega_farm_time_local = mega_farm_time_utc.astimezone(
                local_timezone)

            # Первый обязательный запуск
            end_second_launch = mega_farm_time_local - \
                timedelta(hours=8, minutes=30)
            start_second_launch = end_second_launch - timedelta(minutes=30)

            if current_time < end_second_launch:
                if start_second_launch < end_second_launch:
                    second_launch = start_second_launch + timedelta(
                        seconds=random.randint(
                            0, int((end_second_launch - start_second_launch).total_seconds()))
                    )
                    if second_launch > current_time:
                        schedules.append(second_launch)

            # Второй обязательный запуск
            start_first_launch = mega_farm_time_local
            end_first_launch = mega_farm_time_local + timedelta(minutes=25)
            first_launch = start_first_launch + timedelta(
                seconds=random.randint(
                    0, int((end_first_launch - start_first_launch).total_seconds()))
            )
            if first_launch > current_time:
                schedules.append(first_launch)

            # Случайные запуски до времени мегафарма - 8.5 часов
            additional_start = current_time + \
                timedelta(minutes=random.randint(10, 30))
            while additional_start < end_second_launch:
                next_random_time = additional_start + \
                    timedelta(hours=random.randint(2, 4))
                if next_random_time < end_second_launch and next_random_time >= additional_start + timedelta(hours=2):
                    schedules.append(next_random_time)
                additional_start = next_random_time

            # Случайные запуски после мегафарма
            current_time_after_first = first_launch + \
                timedelta(hours=random.randint(3, 5))
            max_time = mega_farm_time_local + timedelta(hours=12)
            while current_time_after_first < max_time:
                next_random_time = current_time_after_first + \
                    timedelta(hours=random.randint(3, 5))
                if next_random_time >= current_time_after_first + timedelta(hours=2):
                    schedules.append(next_random_time)
                current_time_after_first = next_random_time

            # Сортируем расписание
            schedules = [time for time in schedules if time > current_time]
            schedules.sort()

            # Добавляем индивидуальный сдвиг времени для каждого DAO
            # Добавляем сдвиг от 0 до 2 минут
            shift_seconds = random.randint(0, 120)
            schedules = [time + timedelta(seconds=shift_seconds)
                         for time in schedules]

            dao_schedules[dao_id] = schedules

        if not specific_dao_id:  # Логируем расписания только при первом вызове
            self.log(f"{base.yellow}Full schedules for all DAO:")
            for dao_id, times in dao_schedules.items():
                self.log(f"{base.yellow}DAO ID: {dao_id}")
                for time in times:
                    self.log(f"  - {time.strftime('%Y-%m-%d %H:%M:%S %z')}")

        return dao_schedules

    # Метод для логирования

    @staticmethod
    def log(message):
        # Замените на base.log, если требуется
        base.log(f"{base.yellow}{message}")

    def process_dao(self, dao_id, accounts_data, dao_schedules):
        """Обрабатывает запуск одного DAO."""
        current_time = datetime.now(get_localzone())

        # Загружаем аккаунты
        data = open(self.data_file, "r").read().splitlines()
        data = [line for line in data if line.strip()]
        threads = []

        # Фильтруем аккаунты для запуска только по текущему DAO
        dao_accounts = []
        for account_data in data:
            account_key = str(data.index(account_data))

            if account_key not in accounts_data:
                try:
                    accounts_data[account_key] = {
                        "headers": get_headers(),
                        "proxy": random.choice(self.connected_proxies) if self.connected_proxies else None
                    }
                    # Сохраняем новые данные сразу
                    self.save_accounts(accounts_data)
                except Exception as e:
                    self.log(f"Error initializing account {account_key}: {e}")
                    continue

            account_headers = accounts_data[account_key].get("headers")
            account_proxy = accounts_data[account_key].get("proxy")

            if not account_headers or not account_proxy:
                self.log(
                    f"Skipping account {account_key}: Missing headers or proxy")
                continue

            dao_id_for_account, _ = self.get_current_dao(
                headers=account_headers, proxies=account_proxy)

            if dao_id_for_account == dao_id:
                dao_accounts.append(account_data)

        self.account_info_results.clear()

        # Создаем потоки только для аккаунтов, относящихся к текущему DAO
        for account_data in dao_accounts:
            account_key = str(data.index(account_data))
            account_headers = accounts_data[account_key].get("headers")
            account_proxy = accounts_data[account_key].get("proxy")

            thread = threading.Thread(target=self.process_account, args=(
                account_data, account_proxy, account_headers))
            threads.append(thread)

        # Запускаем потоки
        for thread in threads:
            thread.start()

        # Обрабатываем завершение потоков
        for thread in threads:
            thread.join()

        # Удаляем завершённый запуск из расписания
        dao_schedules[dao_id] = [
            scheduled_time for scheduled_time in dao_schedules[dao_id]
            if scheduled_time > current_time
        ]

        if not dao_schedules[dao_id]:
            self.log(
                f"{base.yellow}Regenerating schedule for DAO ID {dao_id} due to empty schedule..."
            )
            dao_schedules[dao_id] = self.get_dao_schedules(
                specific_dao_id=dao_id).get(dao_id, [])

        self.log(
            f"{base.green}Completed launch for DAO ID {dao_id}."
        )
        # Печатаем результаты
        base.log(self.line)
        base.log(f"{base.green}Account information summary:")
        time.sleep(2)
        base.log(
            f"\033[36m{'Username':<20}\033[36m{'Coins':<10}\033[36m{'Energy':<10}\033[36m{'Max Energy':<10}")
        base.log("-" * 50)

        # Сортируем по количеству монет (coins)
        for account in sorted(self.account_info_results, key=lambda x: x["coins"], reverse=True):
            user_name = account["user_name"]
            coins = account["coins"]
            energy = account["energy"]
            max_energy = account["max_energy"]

            base.log(
                f"\033[36m{user_name:<20}\033[37m{coins:<10}\033[37m{energy:<10}\033[37m{max_energy:<10}")
        base.log(self.line)

    def main(self):
        """Основной цикл работы скрипта."""
        accounts_file = "accounts.json"

        def load_accounts():
            if os.path.exists(accounts_file):
                with open(accounts_file, "r") as f:
                    return json.load(f)
            return {}

        def save_accounts(accounts_data):
            with open(accounts_file, "w") as f:
                json.dump(accounts_data, f, indent=4)

        # Загружаем существующие данные аккаунтов
        accounts_data = load_accounts()
        # Загружаем аккаунты
        data = open(self.data_file, "r").read().splitlines()
        data = [line for line in data if line.strip()]
        for account_data in data:
            account_key = str(data.index(account_data))

            if account_key not in accounts_data:
                if not self.create_new_accoint_json:
                    self.log(
                        "Getting information about the dao and creating a configuration file.  Wait for it...")
                    dao_accounts = []
                    self.connect_all_proxies()
                    dao_id = []
                    self.create_new_accoint_json = True
                try:
                    accounts_data[account_key] = {
                        "headers": get_headers(),
                        "proxy": random.choice(self.connected_proxies) if self.connected_proxies else None
                    }
                    # Сохраняем новые данные сразу
                    save_accounts(accounts_data)
                    account_headers = accounts_data[account_key].get("headers")
                    account_proxy = accounts_data[account_key].get("proxy")
                    if not account_headers or not account_proxy:
                        self.log(
                            f"Skipping account {account_key}: Missing headers or proxy")
                        continue
                    dao_id_for_account, _ = self.create_new_dao(
                        account_data=account_data, headers=account_headers, proxies=account_proxy)
                    save_accounts(accounts_data)
                    if dao_id_for_account == dao_id:
                        dao_accounts.append(account_data)
                except Exception as e:
                    self.log(f"Error initializing account {account_key}: {e}")
                    continue

        # Группируем DAO и генерируем расписание
        self.group_all_dao_and_syndicates(accounts_data)
        dao_schedules = self.get_dao_schedules()

        while True:
            try:
                current_time = datetime.now(get_localzone())

                # Ищем ближайшее время запуска и соответствующие DAO
                next_schedules = [
                    (scheduled_time, dao_id) for dao_id, times in dao_schedules.items()
                    for scheduled_time in times if scheduled_time > current_time
                ]

                if not next_schedules:
                    self.log("No upcoming schedules. Regenerating schedules...")
                    dao_schedules = self.get_dao_schedules()
                    continue

                # Группируем DAO с одинаковым временем запуска
                next_schedules.sort(key=lambda x: x[0])
                next_time = next_schedules[0][0]
                daos_to_launch = [
                    dao_id for scheduled_time, dao_id in next_schedules
                    if scheduled_time == next_time
                ]

                wait_time = (next_time - current_time).total_seconds()
                # self.log(
                #     f"{base.yellow}Next launch for DAO IDs {daos_to_launch} at {next_time.strftime('%Y-%m-%d %H:%M:%S')} (local time)"
                # )
                self.log(f"{base.yellow}Next scheduled launches for all DAO:")
                for dao_id, times in dao_schedules.items():
                    next_time = min(
                        (scheduled_time for scheduled_time in times if scheduled_time > current_time), default=None)
                    if next_time:
                        self.log(
                            f"{base.yellow}DAO ID {dao_id}: {next_time.strftime('%Y-%m-%d %H:%M:%S %z')}"
                        )
                while wait_time > 0:
                    if keyboard.is_pressed('ctrl+shift+s'):
                        self.log("Forced start initiated by user.")
                        break
                    time.sleep(1)
                    wait_time -= 1

                # Подключаем все доступные прокси
                self.connect_all_proxies()

                # Запуск DAO в параллельных потоках
                with ThreadPoolExecutor(max_workers=len(daos_to_launch)) as executor:
                    for dao_id in daos_to_launch:
                        executor.submit(self.process_dao, dao_id,
                                        accounts_data, dao_schedules)

                # Сохраняем изменения в аккаунтах после обработки всех DAO
                save_accounts(accounts_data)

            except KeyboardInterrupt:
                self.log("Script interrupted by user. Exiting...")
                sys.exit()
            except Exception as e:
                self.log(f"Unexpected error: {e}")


if __name__ == "__main__":
    try:
        txd = TONxDAO()
        txd.main()
    except KeyboardInterrupt:
        sys.exit()
