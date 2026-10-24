import asyncio
import logging
from dotenv import load_dotenv

from src.crawler import PlaywrightAICrawler
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
    logger.info("🚀 Bắt đầu chu trình tự động hóa học tập mỗi ngày...")

    # 1. Cào dữ liệu web bằng Playwright (lấy 10 bài để có đủ bài mới sau khi khử trùng lặp)
    crawler = PlaywrightAICrawler(headless=True)
    raw_papers = await crawler.crawl_huggingface_papers(max_items=10)

    # 2. Khử trùng lặp: Lọc các bài báo chưa từng gửi trong quá khứ
    history_manager = HistoryManager()
    selected_papers = history_manager.filter_unseen(raw_papers, max_items=5)
    formatted_data = crawler.format_for_llm(selected_papers)

    # 3. Biên tập và lọc tin rác bằng Gemini Flash
    generator = DigestGenerator()
    digest_html = generator.generate(formatted_data)

    # 4. Gửi thông báo đến Telegram
    sender = TelegramSender()
    success = await sender.send_message(digest_html)

    if success:
        # 5. Lưu lại lịch sử bài đã gửi để không bị lặp lại vào ngày mai
        history_manager.save_history(selected_papers)
        logger.info("🎉 Chu trình hoàn thành xuất sắc!")
    else:
        logger.warning("⚠️ Chu trình hoàn tất nhưng gặp sự cố khi gửi tin nhắn.")

def main():
    asyncio.run(run_pipeline())

if __name__ == "__main__":
    main()
