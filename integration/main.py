from datetime import datetime, timedelta

import requests
import logging

FORMAT = "%(asctime)s | %(levelname)-5s | %(message)s"

logging.basicConfig(format=FORMAT, datefmt="%I:%M:%S %p")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


BIG_CHAT_API = "http://localhost:8267"
OUR_API = "http://localhost:8266"
DELTA_SECONDS = 10


def process_events(events):
    for event in events:
        if event["event_name"] == "START":
            data = {"external_id": str(event["conversation_id"]), "started_at": datetime.now().isoformat()}
            chat = requests.post(f"{OUR_API}/chats", json=data)
            logger.info(f"Created chat {chat.json()['chat_id']}.")


def main(start_at, end_at):
    logger.info(f"Retrieving BigChat from {start_at} to {end_at}")
    response = requests.get(f"{BIG_CHAT_API}/events", params={"start_at": start_at, "end_at": end_at})
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
    end_at = datetime.now()
    logger.info(f"Give me {DELTA_SECONDS}s please")
    while True:
        if datetime.now() >= end_at + timedelta(seconds=DELTA_SECONDS):
            start_at = end_at
            end_at = start_at + timedelta(seconds=DELTA_SECONDS)
            main(start_at, end_at)
