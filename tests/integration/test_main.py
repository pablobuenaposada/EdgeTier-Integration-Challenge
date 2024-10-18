from unittest.mock import MagicMock, call, patch

import pytest

from integration import main
from integration.constants import BIG_CHAT_API, OUR_API
from integration.events.constants import (EVENT_END, EVENT_MESSAGE,
                                          EVENT_START, EVENT_TRANSFER)
from integration.events.utils import chat_cache

CONVERSATION_ID = 12345
START_AT = "2024-10-18 00:00:00"
END_AT = "2024-10-18 00:00:10"
EVENT_AT = 1729225018
CHAT_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
MESSAGE = "foo bar"
AGENT_ID = "efa505ac-d1b6-4b83-92f4-2f67ef03aff9"
AGENT_NAME = "Jhon"
EMAIL_NAME = "jhon@domain.com"


class TestMainStart:
    @patch("requests.get")
    @patch("requests.post")
    def test_start_existent_agent(self, m_post, m_get):
        m_get.side_effect = [
            MagicMock(
                json=lambda: {
                    "events": [{"event_name": EVENT_START, "conversation_id": CONVERSATION_ID, "event_at": EVENT_AT}]
                },
                status_code=200,
            ),
            MagicMock(json=lambda: {"advisor_id": "foo"}, status_code=200),
            MagicMock(json=lambda: {"name": AGENT_NAME, "email_address": EMAIL_NAME}, status_code=200),
            MagicMock(json=lambda: [{"agent_id": AGENT_ID}], status_code=200),
        ]
        m_post.return_value = MagicMock(json=lambda: {"chat_id": CHAT_ID}, status_code=201)

        main.main(START_AT, END_AT)

        assert m_get.call_args_list == [
            call(f"{BIG_CHAT_API}/events", params={"start_at": START_AT, "end_at": END_AT}),
            call(f"{BIG_CHAT_API}/conversations/{CONVERSATION_ID}"),
            call(f"{BIG_CHAT_API}/advisors/foo"),
            call(f"{OUR_API}/agents?email={EMAIL_NAME}"),
        ]
        assert m_post.call_args_list == [
            call(
                f"{OUR_API}/chats",
                json={"external_id": str(CONVERSATION_ID), "started_at": EVENT_AT, "agent_id": AGENT_ID},
            ),
        ]

    @patch("requests.get")
    @patch("requests.post")
    def test_start_non_existent_agent(self, m_post, m_get):
        m_get.side_effect = [
            MagicMock(
                json=lambda: {
                    "events": [{"event_name": EVENT_START, "conversation_id": CONVERSATION_ID, "event_at": EVENT_AT}]
                },
                status_code=200,
            ),
            MagicMock(json=lambda: {"advisor_id": "foo"}, status_code=200),
            MagicMock(json=lambda: {"name": AGENT_NAME, "email_address": EMAIL_NAME}, status_code=200),
            MagicMock(json=lambda: [], status_code=200),
        ]
        m_post.side_effect = [
            MagicMock(json=lambda: {"agent_id": AGENT_ID}, status_code=201),
            MagicMock(json=lambda: {"chat_id": CHAT_ID}, status_code=201),
        ]

        main.main(START_AT, END_AT)

        assert m_get.call_args_list == [
            call(f"{BIG_CHAT_API}/events", params={"start_at": START_AT, "end_at": END_AT}),
            call(f"{BIG_CHAT_API}/conversations/{CONVERSATION_ID}"),
            call(f"{BIG_CHAT_API}/advisors/foo"),
            call(f"{OUR_API}/agents?email={EMAIL_NAME}"),
        ]
        assert m_post.call_args_list == [
            call(f"{OUR_API}/agents", json={"name": AGENT_NAME, "email": EMAIL_NAME}),
            call(
                f"{OUR_API}/chats",
                json={"external_id": str(CONVERSATION_ID), "started_at": EVENT_AT, "agent_id": AGENT_ID},
            ),
        ]


class TestMainEnd:
    @patch("requests.get")
    @patch("requests.patch")
    @pytest.mark.parametrize(
        "chat_retrieval_response",
        (
            [{"chat_id": CHAT_ID}],  # chat found
            [],  # chat not found
        ),
    )
    def test_end(self, m_patch, m_get, chat_retrieval_response):
        chat_cache.clear()
        m_get.side_effect = [
            MagicMock(
                json=lambda: {
                    "nextPageUrl": None,
                    "events": [{"event_name": EVENT_END, "conversation_id": CONVERSATION_ID, "event_at": EVENT_AT}],
                },
                status_code=200,
            ),
            MagicMock(json=lambda: chat_retrieval_response, status_code=200),
        ]

        main.main(START_AT, END_AT)

        assert m_get.call_args_list == [
            call(f"{BIG_CHAT_API}/events", params={"start_at": START_AT, "end_at": END_AT}),
            call(f"{OUR_API}/chats?external_id={CONVERSATION_ID}"),
        ]
        if chat_retrieval_response:
            assert m_patch.call_args_list == [call(f"{OUR_API}/chats/{CHAT_ID}", json={"ended_at": EVENT_AT})]
        else:
            assert m_patch.call_args_list == []


class TestMainMessage:
    @patch("requests.get")
    @patch("requests.post")
    @pytest.mark.parametrize(
        "chat_retrieval_response",
        (
            [{"chat_id": CHAT_ID}],  # chat found
            [],  # chat not found
        ),
    )
    def test_message(self, m_post, m_get, chat_retrieval_response):
        chat_cache.clear()
        m_get.side_effect = [
            MagicMock(
                json=lambda: {
                    "nextPageUrl": None,
                    "events": [
                        {
                            "event_name": EVENT_MESSAGE,
                            "conversation_id": CONVERSATION_ID,
                            "event_at": EVENT_AT,
                            "data": {"message": "foo bar"},
                        }
                    ],
                },
                status_code=200,
            ),
            MagicMock(json=lambda: chat_retrieval_response, status_code=200),
        ]

        main.main(START_AT, END_AT)

        assert m_get.call_args_list == [
            call(f"{BIG_CHAT_API}/events", params={"start_at": START_AT, "end_at": END_AT}),
            call(f"{OUR_API}/chats?external_id={CONVERSATION_ID}"),
        ]
        if chat_retrieval_response:
            assert m_post.call_args_list == [
                call(f"{OUR_API}/chats/{CHAT_ID}/messages", json={"sent_at": EVENT_AT, "text": MESSAGE})
            ]
        else:
            assert m_post.call_args_list == []


class TestMainTransfer:
    @patch("requests.get")
    @patch("requests.post")
    @patch("requests.patch")
    @pytest.mark.parametrize(
        "chat_retrieval_response",
        (
            [{"chat_id": CHAT_ID}],  # chat found
            [],  # chat not found
        ),
    )
    def test_transfer_existent_agent(self, m_patch, m_post, m_get, chat_retrieval_response):
        chat_cache.clear()
        m_get.side_effect = [
            MagicMock(
                json=lambda: {
                    "nextPageUrl": None,
                    "events": [
                        {
                            "event_name": EVENT_TRANSFER,
                            "conversation_id": CONVERSATION_ID,
                            "event_at": EVENT_AT,
                            "data": {"new_advisor_id": "1"},
                        }
                    ],
                },
                status_code=200,
            ),
            MagicMock(json=lambda: chat_retrieval_response, status_code=200),
            MagicMock(json=lambda: {"name": AGENT_NAME, "email_address": EMAIL_NAME}, status_code=200),
            MagicMock(json=lambda: [{"agent_id": AGENT_ID}], status_code=200),
        ]

        main.main(START_AT, END_AT)

        if chat_retrieval_response:
            assert m_get.call_args_list == [
                call(f"{BIG_CHAT_API}/events", params={"start_at": START_AT, "end_at": END_AT}),
                call(f"{OUR_API}/chats?external_id={CONVERSATION_ID}"),
                call(f"{BIG_CHAT_API}/advisors/1"),
                call(f"{OUR_API}/agents?email={EMAIL_NAME}"),
            ]
            assert m_patch.call_args_list == [call(f"{OUR_API}/chats/{CHAT_ID}", json={"agent_id": AGENT_ID})]
            assert m_post.call_args_list == []
        else:
            assert m_get.call_args_list == [
                call(f"{BIG_CHAT_API}/events", params={"start_at": START_AT, "end_at": END_AT}),
                call(f"{OUR_API}/chats?external_id={CONVERSATION_ID}"),
            ]
            assert m_patch.call_args_list == []
            assert m_post.call_args_list == []

    @patch("requests.get")
    @patch("requests.post")
    @patch("requests.patch")
    @pytest.mark.parametrize(
        "chat_retrieval_response",
        (
            [{"chat_id": CHAT_ID}],  # chat found
            [],  # chat not found
        ),
    )
    def test_transfer_non_existent_agent(self, m_patch, m_post, m_get, chat_retrieval_response):
        chat_cache.clear()
        m_get.side_effect = [
            MagicMock(
                json=lambda: {
                    "nextPageUrl": None,
                    "events": [
                        {
                            "event_name": EVENT_TRANSFER,
                            "conversation_id": CONVERSATION_ID,
                            "event_at": EVENT_AT,
                            "data": {"new_advisor_id": "1"},
                        }
                    ],
                },
                status_code=200,
            ),
            MagicMock(json=lambda: chat_retrieval_response, status_code=200),
            MagicMock(json=lambda: {"name": AGENT_NAME, "email_address": EMAIL_NAME}, status_code=200),
            MagicMock(json=lambda: [], status_code=200),
        ]
        m_post.return_value = MagicMock(json=lambda: {"agent_id": AGENT_ID}, status_code=201)

        main.main(START_AT, END_AT)

        if chat_retrieval_response:
            assert m_get.call_args_list == [
                call(f"{BIG_CHAT_API}/events", params={"start_at": START_AT, "end_at": END_AT}),
                call(f"{OUR_API}/chats?external_id={CONVERSATION_ID}"),
                call(f"{BIG_CHAT_API}/advisors/1"),
                call(f"{OUR_API}/agents?email={EMAIL_NAME}"),
            ]
            assert m_patch.call_args_list == [call(f"{OUR_API}/chats/{CHAT_ID}", json={"agent_id": AGENT_ID})]
            assert m_post.call_args_list == [call(f"{OUR_API}/agents", json={"name": AGENT_NAME, "email": EMAIL_NAME})]
        else:
            assert m_get.call_args_list == [
                call(f"{BIG_CHAT_API}/events", params={"start_at": START_AT, "end_at": END_AT}),
                call(f"{OUR_API}/chats?external_id={CONVERSATION_ID}"),
            ]
            assert m_patch.call_args_list == []
            assert m_post.call_args_list == []


class TestMainPagination:
    @patch("requests.get")
    @patch("requests.post")
    def test_pagination(self, m_post, m_get):
        m_get.side_effect = [
            MagicMock(
                json=lambda: {
                    "nextPageUrl": "whatever",
                    "events": [{"event_name": EVENT_START, "conversation_id": CONVERSATION_ID, "event_at": EVENT_AT}],
                },
                status_code=200,
            ),
            MagicMock(json=lambda: {"advisor_id": "foo"}, status_code=200),
            MagicMock(json=lambda: {"name": AGENT_NAME, "email_address": EMAIL_NAME}, status_code=200),
            MagicMock(json=lambda: [{"agent_id": AGENT_ID}], status_code=200),
            MagicMock(
                json=lambda: {
                    "nextPageUrl": None,
                    "events": [
                        {"event_name": EVENT_START, "conversation_id": CONVERSATION_ID + 1, "event_at": EVENT_AT + 1}
                    ],
                },
                status_code=200,
            ),
            MagicMock(json=lambda: {"advisor_id": "foo"}, status_code=200),
            MagicMock(json=lambda: {"name": AGENT_NAME, "email_address": EMAIL_NAME}, status_code=200),
            MagicMock(json=lambda: [{"agent_id": AGENT_ID}], status_code=200),
        ]

        main.main(START_AT, END_AT)

        assert m_get.call_args_list == [
            call(f"{BIG_CHAT_API}/events", params={"start_at": START_AT, "end_at": END_AT}),
            call(f"{BIG_CHAT_API}/conversations/{CONVERSATION_ID}"),
            call(f"{BIG_CHAT_API}/advisors/foo"),
            call(f"{OUR_API}/agents?email={EMAIL_NAME}"),
            call("whatever"),
            call(f"{BIG_CHAT_API}/conversations/{CONVERSATION_ID + 1}"),
            call(f"{BIG_CHAT_API}/advisors/foo"),
            call(f"{OUR_API}/agents?email={EMAIL_NAME}"),
        ]
        assert m_post.call_args_list == [
            call(
                f"{OUR_API}/chats",
                json={"external_id": str(CONVERSATION_ID), "started_at": EVENT_AT, "agent_id": AGENT_ID},
            ),
            call(
                f"{OUR_API}/chats",
                json={"external_id": str(CONVERSATION_ID + 1), "started_at": EVENT_AT + 1, "agent_id": AGENT_ID},
            ),
        ]
