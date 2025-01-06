import requests
import time

from secretniy import base


def get_info(token, proxies=None, headers=None):
    # Добавляем параметр для предотвращения кэширования
    url = f"https://app.production.tonxdao.app/api/v1/profile?nocache={int(time.time() * 1000)}"

    try:
        # Добавляем токен в заголовки, если он передан
        if token:
            if headers is None:
                headers = {}
            headers["Authorization"] = f"Bearer {token}"
            headers["Referer"] = "https://app.production.tonxdao.app/syndicates"

        # Преобразование прокси в формат, поддерживаемый requests
        formatted_proxies = None
        if proxies and proxies["protocol"] == "socks5":
            formatted_proxies = {
                "http": f"socks5://{proxies['proxy_auth'][0]}:{proxies['proxy_auth'][1]}@{proxies['proxy_host']}:{proxies['proxy_port']}",
                "https": f"socks5://{proxies['proxy_auth'][0]}:{proxies['proxy_auth'][1]}@{proxies['proxy_host']}:{proxies['proxy_port']}",
            }

        # Логируем использование прокси для диагностики
        # if formatted_proxies:
        #     base.log(f"{base.blue}Using SOCKS5 proxy: {formatted_proxies}")

        # Отправляем запрос
        response = requests.get(
            url=url, headers=headers, proxies=formatted_proxies, timeout=20
        )
        response.raise_for_status()  # Вызывает исключение при HTTP ошибке

        # Парсинг ответа
        data = response.json()

        # Проверка структуры данных
        dao_id = data.get("dao_id")
        coins = data.get("coins", 0)
        energy = data.get("energy", 0)
        max_energy = data.get("max_energy", 0)
        user_name = data.get("display_name", "").replace("@", "")

        if not dao_id or not user_name:
            base.log(f"{base.red}Invalid response data: {data}")
            return None

        # base.log(
        #     f"{base.green}Fetched account info: DAO ID={dao_id}, Username={user_name}, Coins={coins}, Energy={energy}/{max_energy}"
        # )
        return dao_id, user_name, coins, energy, max_energy

    except requests.exceptions.RequestException as req_err:
        base.log(f"{base.red}HTTP Request error: {req_err}")
    except json.JSONDecodeError as json_err:
        base.log(f"{base.red}JSON parsing error: {json_err}")
    except Exception as e:
        base.log(f"{base.red}Unexpected error in get_info: {e}")
    finally:
        pass
        # base.log(
        #     f"{base.yellow}Ensure headers are passed as a dictionary and include 'Authorization'."
        # )

    return None
