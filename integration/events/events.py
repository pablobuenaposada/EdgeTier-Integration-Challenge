from datetime import datetime

import requests

from integration.constants import OUR_API
from integration.events.constants import EVENT_START


def create_chat(external_id, started_at, logger):
    data = {"external_id": external_id, "started_at": started_at}
    chat = requests.post(f"{OUR_API}/chats", json=data)
    logger.info(f"Created chat {chat.json()['chat_id']}.")


def process_events(events, logger):
    for event in events:
        if event["event_name"] == EVENT_START:
            create_chat(str(event["conversation_id"]), datetime.now().isoformat(), logger)
