import requests

from config.settings import VK_GROUP_ID, VK_TOKEN

VK_URL = "https://api.vk.ru/method"

API_VERSION = "5.199"


def make_vk_call(method: str, *args, **params) -> dict:
    URL = f"{VK_URL}/{method}"
    params["access_token"] = VK_TOKEN
    params["v"] = API_VERSION
    for key, value in list(params.items()):
        if isinstance(value, (list, tuple, set)):
            params[key] = ",".join(map(str, value))
    try:
        r = requests.get(URL, params=params)
        vk_response = r.json()
    except Exception as exc:
        print(f"Exception - {exc}")

    return vk_response


def get_posts(group_id=VK_GROUP_ID, count=20):
    api_response = make_vk_call("wall.get", owner_id=group_id, count=count)
    if not api_response:
        return []
    return api_response["response"]["items"]


def get_comments(post_id, last_comment_id, group_id=VK_GROUP_ID, count=100):
    api_response = make_vk_call(
        "wall.getComments",
        owner_id=group_id,
        post_id=post_id,
        count=count,
        sort="asc",
        start_comment_id=last_comment_id,
    )
    if not api_response:
        return []
    comments = api_response["response"]["items"]
    if last_comment_id:
        comments = comments[1:]
    return comments


def get_user_name(user_id):
    api_response = make_vk_call("users.get", user_ids=user_id)
    if not api_response:
        return "Неизвестный пользователь"
    user = api_response["response"][0]
    first_name = user.get("first_name")
    last_name = user.get("last_name")
    user_name = f"{first_name} {last_name}"
    return user_name


def get_group_name(group_id):
    api_response = make_vk_call("groups.getById", group_id=group_id)
    if not api_response:
        return "Неизвестное сообщество"
    group_name = api_response["response"]["groups"][0]["name"]
    return group_name


def get_users_names(users_id):
    api_response = make_vk_call("users.get", user_ids=users_id)
    if not api_response:
        return {}
    users = api_response["response"]
    return {
        user["id"]: f"{user.get("first_name")} {user.get("last_name")}"
        for user in users
    }


def get_groups_names(group_ids):
    api_response = make_vk_call("groups.getById", group_ids=group_ids)
    if not api_response:
        return {}
    groups = api_response["response"]["groups"]
    return {group["id"]: group["name"] for group in groups}
