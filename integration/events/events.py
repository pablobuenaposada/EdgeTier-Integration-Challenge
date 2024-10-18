import requests

from integration.constants import OUR_API
from integration.events import constants


def create_chat(external_id, started_at, logger):
    response = requests.post(f"{OUR_API}/chats", json={"external_id": external_id, "started_at": started_at})
    response.raise_for_status()
    logger.info(f"Created chat {response.json()['chat_id']}")


def end_chat(external_id, ended_at, logger):
    response = requests.get(f"{OUR_API}/chats?external_id={external_id}")
    response.raise_for_status()
    response = response.json()
    if len(response) == 1:
        chat_id = response[0]["chat_id"]
        response = requests.patch(f"{OUR_API}/chats/{chat_id}", json={"ended_at": ended_at})
        response.raise_for_status()
        logger.info(f"Ended chat {chat_id}")
    else:
        logger.info(f"Chat for ending not found")


def process_events(events, logger):
    for event in events:
        match event["event_name"]:
            case constants.EVENT_START:
                create_chat(str(event["conversation_id"]), event["event_at"], logger)
            case constants.EVENT_END:
                end_chat(str(event["conversation_id"]), event["event_at"], logger)
