from unittest.mock import MagicMock, call, patch

import pytest

from integration import main
from integration.constants import BIG_CHAT_API, OUR_API
from integration.events.constants import EVENT_END, EVENT_MESSAGE, EVENT_START

CONVERSATION_ID = 12345
START_AT = "2024-10-18 00:00:00"
END_AT = "2024-10-18 00:00:10"
EVENT_AT = 1729225018
CHAT_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
MESSAGE = "foo bar"


class TestMain:

    @patch("requests.get")
    @patch("requests.post")
    def test_start(self, m_post, m_get):
        m_get.return_value = MagicMock(
            json=lambda: {
                "events": [{"event_name": EVENT_START, "conversation_id": CONVERSATION_ID, "event_at": EVENT_AT}]
            },
            status_code=200,
        )

        main.main(START_AT, END_AT)

        m_get.assert_called_once_with(f"{BIG_CHAT_API}/events", params={"start_at": START_AT, "end_at": END_AT})
        m_post.assert_called_once_with(
            f"{OUR_API}/chats", json={"external_id": str(CONVERSATION_ID), "started_at": EVENT_AT}
        )

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
            MagicMock(
                json=lambda: {
                    "nextPageUrl": None,
                    "events": [
                        {"event_name": EVENT_START, "conversation_id": CONVERSATION_ID + 1, "event_at": EVENT_AT + 1}
                    ],
                },
                status_code=200,
            ),
        ]

        main.main(START_AT, END_AT)

        assert m_get.call_args_list == [
            call(f"{BIG_CHAT_API}/events", params={"start_at": START_AT, "end_at": END_AT}),
            call("whatever"),
        ]
        assert m_post.call_args_list == [
            call(f"{OUR_API}/chats", json={"external_id": str(CONVERSATION_ID), "started_at": EVENT_AT}),
            call(f"{OUR_API}/chats", json={"external_id": str(CONVERSATION_ID + 1), "started_at": EVENT_AT + 1}),
        ]
