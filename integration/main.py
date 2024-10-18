import logging
from datetime import datetime, timedelta

import requests

from integration.constants import BIG_CHAT_API, DELTA_SECONDS
from integration.events.events import process_events

FORMAT = "%(asctime)s | %(levelname)-5s | %(message)s"

logging.basicConfig(format=FORMAT, datefmt="%I:%M:%S %p")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def main(start_at, end_at):
    logger.info(f"Retrieving BigChat from {start_at} to {end_at}")
    response = requests.get(f"{BIG_CHAT_API}/events", params={"start_at": start_at, "end_at": end_at})
    response.raise_for_status()
    response_data = response.json()
    process_events(response_data["events"], logger)

    # if more pages found we process also those
    next_page_url = response_data.get("nextPageUrl")
    while next_page_url:
        response = requests.get(next_page_url)
        response.raise_for_status()
        response_data = response.json()
        process_events(response_data["events"], logger)
        next_page_url = response_data.get("nextPageUrl")


if __name__ == "__main__":
    end_at = datetime.now()
    logger.info(f"Give me {DELTA_SECONDS}s please")
    while True:
        if datetime.now() >= end_at + timedelta(seconds=DELTA_SECONDS):
            start_at = end_at
            end_at = start_at + timedelta(seconds=DELTA_SECONDS)
            main(start_at, end_at)
