from integration import main
from unittest.mock import patch, MagicMock, ANY, call

from integration.main import BIG_CHAT_API, OUR_API


class TestMain:

    @patch("requests.get")
    @patch("requests.post")
    def test_start(self, m_post, m_get):
        conversation_id = 12345
        m_get.return_value = MagicMock(
            json=lambda: {"events": [{"event_name": "START", "conversation_id": conversation_id}]}, status_code=200
        )

        main.main()

        m_get.assert_called_once_with(f"{BIG_CHAT_API}/events", params={"start_at": ANY})
        m_post.assert_called_once_with(
            f"{OUR_API}/chats", json={"external_id": str(conversation_id), "started_at": ANY}
        )

    @patch("requests.get")
    @patch("requests.post")
    def test_pagination(self, m_post, m_get):
        conversation_id = 12345
        m_get.side_effect = [
            MagicMock(
                json=lambda: {
                    "nextPageUrl": "whatever",
                    "events": [{"event_name": "START", "conversation_id": conversation_id}],
                },
                status_code=200,
            ),
            MagicMock(
                json=lambda: {
                    "nextPageUrl": None,
                    "events": [{"event_name": "START", "conversation_id": conversation_id + 1}],
                },
                status_code=200,
            ),
        ]

        main.main()

        assert m_get.call_args_list == [
            call(f"{BIG_CHAT_API}/events", params={"start_at": ANY}),
            call("whatever"),
        ]
        assert m_post.call_args_list == [
            call(f"{OUR_API}/chats", json={"external_id": str(conversation_id), "started_at": ANY}),
            call(f"{OUR_API}/chats", json={"external_id": str(conversation_id + 1), "started_at": ANY}),
        ]
