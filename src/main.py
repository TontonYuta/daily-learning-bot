import asyncio
import logging
from dotenv import load_dotenv

from src.crawler import MultiCategoryNewsCrawler
from src.digest import DigestGenerator
from src.telegram_sender import TelegramSender
from src.history import HistoryManager

# Load environment variables from .env file if available
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("DailyBot")

async def run_pipeline():
    logger.info("🚀 Bắt đầu chu trình điểm tin 7 lĩnh vực (Kinh tế, Xã hội, AI, BA, DA, DS, DE)...")

    # 1. Cào dữ liệu đa danh mục (trong nước & quốc tế)
    crawler = MultiCategoryNewsCrawler()
    raw_news = await crawler.crawl_all_categories(limit_per_source=3)

    # 2. Khử trùng lặp: Lọc các bài báo chưa từng gửi trong quá khứ theo từng danh mục
    history_manager = HistoryManager()
    selected_news = history_manager.filter_unseen_by_category(raw_news, max_per_category=2)
    formatted_data = crawler.format_for_llm(selected_news)

    # 3. Biên tập và lọc tin rác bằng Gemini Flash
    generator = DigestGenerator()
    digest_html = generator.generate(formatted_data)

    # 4. Gửi thông báo đến Telegram
    sender = TelegramSender()
    success = await sender.send_message(digest_html)

    if success:
        # 5. Lưu lại lịch sử bài đã gửi để không bị lặp lại vào ngày mai
        history_manager.save_history_from_categories(selected_news)
        logger.info("🎉 Chu trình hoàn thành xuất sắc!")
    else:
        logger.warning("⚠️ Chu trình hoàn tất nhưng gặp sự cố khi gửi tin nhắn.")

def main():
    asyncio.run(run_pipeline())

if __name__ == "__main__":
    main()
