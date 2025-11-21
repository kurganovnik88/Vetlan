import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Простой клиент Telegram Bot API для отправки уведомлений.
    """

    def __init__(self, bot_token: Optional[str], chat_id: Optional[str]):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = (
            f"https://api.telegram.org/bot{bot_token}/sendMessage"
            if bot_token
            else None
        )

    def send(self, text: str, parse_mode: str = "HTML") -> None:
        """
        Отправляет сообщение в Telegram.
        """
        if not self.bot_token or not self.chat_id or not self.api_url:
            logger.warning("TelegramNotifier: токен или chat_id не заданы.")
            return

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        try:
            response = requests.post(self.api_url, data=payload, timeout=5)

            if response.status_code != 200:
                logger.error(
                    "TelegramNotifier: ошибка %s: %s",
                    response.status_code,
                    response.text,
                )
                return

            logger.info("TelegramNotifier: сообщение отправлено.")

        except Exception as exc:
            logger.error("TelegramNotifier: исключение при отправке: %s", exc)
