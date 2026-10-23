import os
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

class TelegramSender:
    """Xử lý gửi tin nhắn bản tin qua Telegram Bot API."""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")

    async def send_message(self, html_content: str) -> bool:
        """Gửi nội dung định dạng HTML đến Telegram. Hỗ trợ chế độ dry-run nếu chưa cấu hình."""
        if not self.bot_token or not self.chat_id:
            logger.info("ℹ️ Chưa cấu hình TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID. Chạy chế độ Dry-Run:")
            print("\n" + "="*50)
            print("--- NỘI DUNG SẼ ĐƯỢC GỬI ĐẾN TELEGRAM ---")
            print(html_content)
            print("="*50 + "\n")
            return True

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": html_content,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    logger.info("✅ Đã gửi bản tin thành công về Telegram!")
                    return True
                else:
                    logger.error(f"❌ Lỗi gửi Telegram: HTTP {res.status_code} - {res.text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Ngoại lệ khi gửi Telegram: {e}")
            return False
