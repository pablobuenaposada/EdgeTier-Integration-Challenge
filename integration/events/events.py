import requests

from integration.constants import OUR_API
from integration.events import constants
from integration.events.utils import search_chat


def create_chat(external_id, event_at, logger):
    response = requests.post(f"{OUR_API}/chats", json={"external_id": external_id, "started_at": event_at})
    response.raise_for_status()
    logger.info(f"Created chat {response.json()['chat_id']}")


def end_chat(external_id, event_at, logger):
    chat_id = search_chat(external_id)
    if chat_id:
        response = requests.patch(f"{OUR_API}/chats/{chat_id}", json={"ended_at": event_at})
        response.raise_for_status()
        logger.info(f"Ended chat {chat_id}")
    else:
        logger.info(f"Chat for ending not found")


def create_message(external_id, message, event_at, logger):
    chat_id = search_chat(external_id)
    if chat_id:
        response = requests.post(f"{OUR_API}/chats/{chat_id}/messages", json={"sent_at": event_at, "text": message})
        response.raise_for_status()
        logger.info(f"Create message for chat {chat_id}")
    else:
        logger.info(f"Chat for message not found")

def process_events(events, logger):
    for event in events:
        match event["event_name"]:
            case constants.EVENT_START:
                create_chat(str(event["conversation_id"]), event["event_at"], logger)
            case constants.EVENT_END:
                end_chat(str(event["conversation_id"]), event["event_at"], logger)
            case constants.EVENT_MESSAGE:
                create_message(event["conversation_id"], event["data"]["message"], event["event_at"], logger)
