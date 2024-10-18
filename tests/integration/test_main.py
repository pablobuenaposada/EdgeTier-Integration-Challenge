from integration import main
from unittest.mock import patch, MagicMock, ANY


class TestMain:
    @patch('requests.get')
    @patch('requests.post')
    def test_start(self, m_post, m_get):
        conversation_id = 12345
        m_get.return_value = MagicMock(
            json=lambda: {"events": [{"event_name": "START", "conversation_id": conversation_id}]},
            status_code=200
        )
        m_post.return_value = MagicMock(
            json=lambda: {"chat_id": "1"},
            status_code=201
        )

        main.main()

        m_get.assert_called_once_with(
            "http://localhost:8267/events",
            params={'start_at': ANY}
        )
        m_post.assert_called_once_with(
            "http://localhost:8266/chats",
            json={"external_id": str(conversation_id), "started_at": ANY}
        )
