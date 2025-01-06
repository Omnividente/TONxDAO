import requests

from secretniy import base


def get_token(data, proxy=None, headers=None):
    url = "https://app.production.tonxdao.app/api/v1/login/web-app"
    payload = {"initData": data}

    try:
        # Проверяем входные данные
        if not headers:
            raise ValueError("Headers must be provided.")
        if proxy and not isinstance(proxy, dict):
            raise ValueError(
                "Proxy must be a dictionary with 'http' and 'https' keys.")

        # Логируем начало запроса
        # base.log(f"{base.blue}Requesting access token...")

        # Выполняем запрос
        response = requests.post(
            url=url, headers=headers, json=payload, proxies=proxy, timeout=20
        )
        response.raise_for_status()  # Вызывает исключение при HTTP ошибке

        # Парсим ответ
        data = response.json()
        token = data.get("access_token")

        if token:
            # base.log(f"{base.green}Access token retrieved successfully.")
            return token
        else:
            base.log(f"{base.red}Failed to retrieve access token: {data}")
            return None
    except requests.exceptions.RequestException as req_err:
        base.log(f"{base.red}HTTP Request error: {req_err}")
    except Exception as e:
        base.log(f"{base.red}Error in get_token: {e}")
    return None


def get_centrifugo_token(token, proxy=None, headers=None):
    url = "https://app.production.tonxdao.app/api/v1/centrifugo-token"

    try:
        # Проверяем входные данные
        if not headers:
            raise ValueError("Headers must be provided.")
        if proxy and not isinstance(proxy, dict):
            raise ValueError(
                "Proxy must be a dictionary with 'http' and 'https' keys.")

        # Выполняем запрос
        formatted_headers = headers if isinstance(
            headers, dict) else headers(token=token)
        response = requests.get(
            url=url, headers=formatted_headers, proxies=proxy, timeout=20
        )
        response.raise_for_status()  # Вызывает исключение при HTTP ошибке

        # Парсим ответ
        data = response.json()
        centrifugo_token = data.get("token")

        if centrifugo_token:
            return centrifugo_token
        else:
            base.log(f"{base.red}Failed to retrieve Centrifugo token: {data}")
            return None
    except requests.exceptions.RequestException as req_err:
        base.log(f"{base.red}HTTP Request error: {req_err}")
    except Exception as e:
        base.log(f"{base.red}Error in get_centrifugo_token: {e}")
    return None
