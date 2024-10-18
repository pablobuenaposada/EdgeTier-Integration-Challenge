import requests

from integration.constants import OUR_API


def search_chat(external_id):
    response = requests.get(f"{OUR_API}/chats?external_id={external_id}")
    response.raise_for_status()
    response = response.json()

    if len(response) == 1:
        return response[0]["chat_id"]
