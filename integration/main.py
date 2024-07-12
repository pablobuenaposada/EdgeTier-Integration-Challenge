from datetime import datetime, timedelta

import requests
import logging

FORMAT = "%(asctime)s | %(levelname)-5s | %(message)s"

logging.basicConfig(format=FORMAT, datefmt="%I:%M:%S %p")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


BIG_CHAT_API = "http://localhost:8267"
OUR_API = "http://localhost:8266"

if __name__ == "__main__":
    # Get events from BigChat.
    parameters = {"start_at": (datetime.now() - timedelta(seconds=10))}
    events = requests.get(f"{BIG_CHAT_API}/events", params=parameters)

    # TODO: This is just an example, feel free to change however you want:
    for event in events.json()["events"]:
        if event["event_name"] == "START":
            # Create a chat.
            data = {"external_id": str(event["conversation_id"]), "started_at": datetime.now().isoformat()}
            chat = requests.post(f"{OUR_API}/chats", json=data)
            logger.info(f"Created chat {chat.json()['chat_id']}.")
