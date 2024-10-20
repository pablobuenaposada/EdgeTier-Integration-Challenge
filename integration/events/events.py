from collections import Counter
from typing import Any, List

import requests

from integration.constants import OUR_API
from integration.events import constants
from integration.events.constants import (EVENT_END_LOG, EVENT_MESSAGE_LOG,
                                          EVENT_START_LOG, EVENT_TRANSFER_LOG)
from integration.events.utils import (search_advisor, search_chat,
                                      search_or_create_agent)


def _create_chat(conversation_id: int, event_at: int, logger: Any) -> None:
    agent_id = search_or_create_agent(search_advisor(conversation_id), logger)
    response = requests.post(
        f"{OUR_API}/chats", json={"external_id": str(conversation_id), "started_at": event_at, "agent_id": agent_id}
    )
    response.raise_for_status()
    logger.info(f"{EVENT_START_LOG} Created chat {response.json()['chat_id']}")


def _end_chat(conversation_id: int, event_at: int, logger: Any) -> None:
    chat_id = search_chat(conversation_id)
    if chat_id:
        response = requests.patch(f"{OUR_API}/chats/{chat_id}", json={"ended_at": event_at})
        response.raise_for_status()
        logger.info(f"{EVENT_END_LOG} Ended chat {chat_id}")
    else:
        logger.warning(f"{EVENT_END_LOG} Chat not found")


def _create_message(conversation_id: int, message: str, event_at: int, logger: Any) -> None:
    chat_id = search_chat(conversation_id)
    if chat_id:
        response = requests.post(f"{OUR_API}/chats/{chat_id}/messages", json={"sent_at": event_at, "text": message})
        response.raise_for_status()
        logger.info(f"{EVENT_MESSAGE_LOG} Create message for chat {chat_id}")
    else:
        logger.warning(f"{EVENT_MESSAGE_LOG} Chat not found")


def _transfer_chat(external_id: int, new_advisor: int, logger: Any) -> None:
    chat_id = search_chat(external_id)
    if chat_id:
        new_agent_id = search_or_create_agent(new_advisor, logger)
        response = requests.patch(f"{OUR_API}/chats/{chat_id}", json={"agent_id": new_agent_id})
        response.raise_for_status()
        logger.info(f"{EVENT_TRANSFER_LOG} Update agent from chat {chat_id}")
    else:
        logger.warning(f"{EVENT_TRANSFER_LOG} Chat not found")


def process_events(events: List, logger: Any) -> None:
    event_counts = Counter(event["event_name"] for event in events)
    summary = ", ".join([f"{count} {event_name}" for event_name, count in event_counts.items()])
    logger.info(f"Found the following events: {summary}")

    for event in events:
        match event["event_name"]:
            case constants.EVENT_START:
                _create_chat(event["conversation_id"], event["event_at"], logger)
            case constants.EVENT_END:
                _end_chat(event["conversation_id"], event["event_at"], logger)
            case constants.EVENT_MESSAGE:
                _create_message(event["conversation_id"], event["data"]["message"], event["event_at"], logger)
            case constants.EVENT_TRANSFER:
                _transfer_chat(event["conversation_id"], event["data"]["new_advisor_id"], logger)
