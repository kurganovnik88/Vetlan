import requests
import logging

logger = logging.getLogger("bot")

class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send(self, text: str):
        """Отправка HTML-сообщения в Telegram"""
        if not self.token or not self.chat_id:
            logger.warning("⚠️ Telegram токен или chat_id не заданы, уведомление не отправлено.")
            return

        try:
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            response = requests.post(self.base_url, json=payload, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Ошибка Telegram API: {response.text}")
        except Exception as e:
            logger.warning(f"Ошибка отправки Telegram-сообщения: {e}")
