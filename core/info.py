import requests
import threading

from secretniy import base
from core.headers import headers


def get_info(token, proxies=None, headers=None, user_agent=None):
    url = "https://app.production.tonxdao.app/api/v1/profile"

    try:
        user_agent = user_agent if user_agent else (headers['User-Agent'] if isinstance(headers, dict) else headers(token)['User-Agent'])
        #base.log(f"{base.blue}Using User-Agent: {user_agent}")
        if isinstance(headers, dict):
            headers['User-Agent'] = user_agent if user_agent else headers['User-Agent']
        response = requests.get(
            url=url, headers=headers, proxies=proxies, timeout=20
        )
        data = response.json()
        dao_id = data["dao_id"]
        coins = data["coins"]
        energy = data["energy"]
        max_energy = data["max_energy"]
        user_name = data["display_name"].replace("@", "")       
        return dao_id, user_name, coins, energy, max_energy 
    except Exception as e:
        base.log(f"{base.red}Error fetching account info: {e}")
        base.log(f"{base.red}Make sure headers are being passed as a dictionary.")
        
        return None
