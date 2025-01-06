from fake_useragent import UserAgent


def get_headers(token=None):
    # Создание объекта UserAgent
    ua = UserAgent()

    # Генерация случайного User-Agent
    user_agent = ua.random

    # Формирование заголовков
    headers = {
        "User-Agent": user_agent,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Connection": "keep-alive",
        "X-Requested-With": "XMLHttpRequest"
    }

    # Добавление токена, если он передан
    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers
