import asyncio
import logging
from dotenv import load_dotenv

from src.crawler import PlaywrightAICrawler
from src.digest import DigestGenerator
from src.telegram_sender import TelegramSender

# Load environment variables from .env file if available
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("DailyBot")

async def run_pipeline():
    logger.info("🚀 Bắt đầu chu trình tự động hóa học tập mỗi ngày...")

    # 1. Cào dữ liệu web bằng Playwright
    crawler = PlaywrightAICrawler(headless=True)
    papers = await crawler.crawl_huggingface_papers(max_items=5)
    formatted_data = crawler.format_for_llm(papers)

    # 2. Biên tập và lọc tin rác bằng Gemini Flash
    generator = DigestGenerator()
    digest_html = generator.generate(formatted_data)

    # 3. Gửi thông báo đến Telegram
    sender = TelegramSender()
    success = await sender.send_message(digest_html)

    if success:
        logger.info("🎉 Chu trình hoàn thành xuất sắc!")
    else:
        logger.warning("⚠️ Chu trình hoàn tất nhưng gặp sự cố khi gửi tin nhắn.")

def main():
    asyncio.run(run_pipeline())

if __name__ == "__main__":
    main()
