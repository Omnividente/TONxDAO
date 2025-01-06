import requests


from secretniy import base


def check_in(token, proxies=None, headers=None):
    url = "https://app.production.tonxdao.app/api/v1/tasks/daily"
    try:
        response = requests.get(
            url=url, headers=headers if isinstance(headers, dict) else headers(token=token), proxies=proxies, timeout=20
        )
        data = response.json()
        status = data["is_available"]

        return status
    except:
        return None


def claim_check_in(token, proxies=None, headers=None):
    url = "https://app.production.tonxdao.app/api/v1/tasks/daily/claim"

    try:
        response = requests.post(
            url=url, headers=headers if isinstance(headers, dict) else headers(token=token), proxies=proxies, timeout=20
        )
        data = response.json()
        status = data["success"]

        return status
    except:
        return None


def process_check_in(token, proxies=None, username=None, headers=None):
    check_in_status = check_in(
        token=token, proxies=proxies, headers=headers)
    if check_in_status:
        start_check_in = claim_check_in(
            token=token, proxies=proxies, headers=headers)
        if start_check_in:
            base.log(
                f"{base.blue}{username} {base.white}Auto Check-in: {base.green}Success")
        else:
            base.log(
                f"{base.blue}{username} {base.white}Auto Check-in: {base.red}Fail")
    else:
        base.log(
            f"{base.blue}{username} {base.white}Auto Check-in: {base.red}Claimed")


def get_task(token, proxies=None, headers=None):
    url = "https://app.production.tonxdao.app/api/v1/tasks"

    try:
        response = requests.get(
            url=url, headers=headers if isinstance(headers, dict) else headers(token=token), proxies=proxies, timeout=20
        )
        data = response.json()

        return data
    except:
        return None


def start_task(token, task_id, proxies=None, headers=None):
    url = f"https://app.production.tonxdao.app/api/v1/tasks/{task_id}/start"

    try:
        response = requests.post(
            url=url, headers=headers if isinstance(headers, dict) else headers(token=token), proxies=proxies, timeout=20
        )
        data = response.json()

        return data
    except:
        return None


def claim_task(token, task_id, proxies=None, headers=None):
    url = f"https://app.production.tonxdao.app/api/v1/tasks/{task_id}/claim"

    try:
        response = requests.post(
            url=url, headers=headers if isinstance(headers, dict) else headers(token=token), proxies=proxies, timeout=20
        )
        data = response.json()

        return data
    except:
        return None


def process_do_task(token, proxies=None, username=None, headers=None):
    task_list = get_task(token=token, proxies=proxies,
                         headers=headers)
    if not task_list:
        base.log(f"{base.red}Failed to retrieve task list for {username}")
        return

    for task in task_list:
        task_id = task["id"]
        task_name = task["name"]
        is_active = task["is_active"]
        is_completed = task["is_completed"]
        is_claimed = task["is_claimed"]
        is_started = task["is_started"]

        if is_active:
            if is_started:
                if is_completed:
                    if is_claimed:
                        base.log(
                            f"{base.blue}{username} {base.white}{task_name}: {base.green}Completed")
                    else:
                        start_claim = claim_task(
                            token=token, task_id=task_id, proxies=proxies, headers=headers
                        )
                        base.log(
                            f"{base.blue}{username} {base.white}{task_name}: {base.yellow}Claiming...")
                else:
                    base.log(
                        f"{base.blue}{username} {base.white}{task_name}: {base.red}Not ready to claim")
            else:
                do_task = start_task(
                    token=token, task_id=task_id, proxies=proxies, headers=headers)
                base.log(
                    f"{base.blue}{username} {base.white}{task_name}: {base.yellow}Starting...")
        else:
            base.log(
                f"{base.blue}{username} {base.white}{task_name}: {base.red}Inactive")
