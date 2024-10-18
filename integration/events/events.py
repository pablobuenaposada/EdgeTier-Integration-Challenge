from datetime import datetime

import requests

from integration.constants import OUR_API
from integration.events.constants import EVENT_START


def process_events(events, logger):
    for event in events:
        if event["event_name"] == EVENT_START:
            data = {"external_id": str(event["conversation_id"]), "started_at": datetime.now().isoformat()}
            chat = requests.post(f"{OUR_API}/chats", json=data)
            logger.info(f"Created chat {chat.json()['chat_id']}.")
