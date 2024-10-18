from datetime import datetime, timedelta

import requests
import logging

FORMAT = "%(asctime)s | %(levelname)-5s | %(message)s"

logging.basicConfig(format=FORMAT, datefmt="%I:%M:%S %p")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


BIG_CHAT_API = "http://localhost:8267"
OUR_API = "http://localhost:8266"


def process_events(events):
    for event in events:
        if event["event_name"] == "START":
            data = {"external_id": str(event["conversation_id"]), "started_at": datetime.now().isoformat()}
            chat = requests.post(f"{OUR_API}/chats", json=data)
            logger.info(f"Created chat {chat.json()['chat_id']}.")


def main():
    parameters = {"start_at": (datetime.now() - timedelta(seconds=10))}
    response = requests.get(f"{BIG_CHAT_API}/events", params=parameters)
    response_data = response.json()
    process_events(response_data["events"])

    # if more pages found we process also those
    next_page_url = response_data.get("nextPageUrl")
    while next_page_url:
        response = requests.get(next_page_url)
        response_data = response.json()
        process_events(response_data["events"])
        next_page_url = response_data.get("nextPageUrl")


if __name__ == "__main__":
    main()
