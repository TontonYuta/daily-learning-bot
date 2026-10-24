import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, List
import httpx
from dotenv import load_dotenv

from src.crawler import MultiCategoryNewsCrawler, DEFAULT_FEED_REGISTRY
from src.digest import DigestGenerator
from src.telegram_sender import TelegramSender
from src.history import HistoryManager, VN_TZ
from src.main import run_pipeline
from google import genai

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("InteractiveBot")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

async def setup_bot_commands(bot_token: Optional[str] = None):
    """Đăng ký danh sách menu lệnh hiển thị trên thanh gõ phím của Telegram."""
    token = bot_token or TELEGRAM_BOT_TOKEN
    if not token:
        return
    url = f"https://api.telegram.org/bot{token}/setMyCommands"
    commands = [
        {"command": "read", "description": "Điểm tin đầy đủ 7 lĩnh vực (kèm link)"},
        {"command": "ai", "description": "Điểm tin chuyên sâu AI & Papers mới"},
        {"command": "data", "description": "Điểm tin Data (BA, DA, DS, DE)"},
        {"command": "kinhte", "description": "Điểm tin Kinh tế (VN & Quốc tế)"},
        {"command": "xahoi", "description": "Điểm tin Xã hội (VN & Quốc tế)"},
        {"command": "math", "description": "Bài học trực giác Toán THPT"},
        {"command": "now", "description": "Kích hoạt gửi ngay bản tin chính thức"},
        {"command": "help", "description": "Xem hướng dẫn & danh sách lệnh"}
    ]
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(url, json={"commands": commands})
            if res.status_code == 200:
                logger.info("✅ Đã đăng ký menu lệnh Telegram thành công!")
    except Exception as e:
        logger.warning(f"Không thể thiết lập menu Telegram: {e}")

async def handle_read_command(chat_id: int):
    """Khi user gõ /read hoặc /baidoc: Cào dữ liệu mới nhất 7 lĩnh vực và sinh bài đọc ngay lập tức."""
    sender = TelegramSender(bot_token=TELEGRAM_BOT_TOKEN, chat_id=str(chat_id))
    await sender.send_message("⏳ <i>Đang cào tin tức mới nhất (Kinh tế, Xã hội, AI, BA, DA, DS, DE) và biên soạn bài đọc cho bạn... Vui lòng đợi trong giây lát!</i>")

    crawler = MultiCategoryNewsCrawler()
    raw_news = await crawler.crawl_all_categories(limit_per_source=3)

    history_manager = HistoryManager()
    selected_news = history_manager.filter_unseen_by_category(raw_news, max_per_category=2)
    formatted_data = crawler.format_for_llm(selected_news)

    generator = DigestGenerator(api_key=GEMINI_API_KEY)
    digest_html = generator.generate(formatted_data)

    success = await sender.send_message(digest_html)
    if success:
        history_manager.save_history_from_categories(selected_news)

async def handle_category_command(chat_id: int, categories: List[str], label: str):
    """Cào và biên soạn nhanh cho một hoặc nhiều danh mục cụ thể theo yêu cầu on-demand."""
    sender = TelegramSender(bot_token=TELEGRAM_BOT_TOKEN, chat_id=str(chat_id))
    await sender.send_message(f"⏳ <i>Đang cào dữ liệu mới nhất cho chuyên mục <b>{label}</b>... Vui lòng đợi trong giây lát!</i>")

    custom_registry = {cat: DEFAULT_FEED_REGISTRY[cat] for cat in categories if cat in DEFAULT_FEED_REGISTRY}
    crawler = MultiCategoryNewsCrawler(feed_registry=custom_registry)
    raw_news = await crawler.crawl_all_categories(limit_per_source=3)

    history_manager = HistoryManager()
    selected_news = history_manager.filter_unseen_by_category(raw_news, max_per_category=2)
    formatted_data = crawler.format_for_llm(selected_news)

    generator = DigestGenerator(api_key=GEMINI_API_KEY)
    digest_html = generator.generate(formatted_data)

    success = await sender.send_message(digest_html)
    if success:
        history_manager.save_history_from_categories(selected_news)

async def handle_math_command(chat_id: int):
    """Khi user gõ /math: Sinh riêng 1 bài toán THPT kết nối với thực tế/AI, ngắn gọn và thực dụng."""
    sender = TelegramSender(bot_token=TELEGRAM_BOT_TOKEN, chat_id=str(chat_id))
    await sender.send_message("📐 <i>Đang chọn 1 chủ đề toán thực dụng cho bạn...</i>")

    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = """
    Bạn là một kỹ sư phần mềm thực chiến. Chọn ngẫu nhiên 1 chủ đề toán THPT (Đạo hàm, Ma trận, Vectơ, Xác suất có điều kiện, Cực trị...).
    Giải thích TRỰC DIỆN, BỎ TOÀN BỘ VĂN VẺ HOA MỸ VÀ TỪ NGỮ AI SLOP (cấm dùng: 'đột phá', 'hãy tưởng tượng', 'then chốt', 'bước ngoặt').

    ĐỊNH DẠNG (HTML Telegram):
    📐 <b>TOÁN THPT & ỨNG DỤNG AI THỰC TẾ</b>
    • <b>Khái niệm:</b> [Tên khái niệm lớp 10, 11 hoặc 12]
    • <b>Ý nghĩa cốt lõi:</b> [1-2 câu trần thuật trần trụi về mặt hình học hoặc số học]
    • <b>AI dùng làm gì:</b> [Chỉ rõ thuật toán AI nào dùng nó và giải quyết khâu nào, không nói chung chung]
    • <b>Ví dụ / Câu hỏi phản xạ:</b> [1 ví dụ số hoặc câu hỏi thực tế ngắn]
    👉 <tg-spoiler>Đáp án: [Giải thích ngắn trong 1 dòng]</tg-spoiler>
    """
    try:
        models_to_try = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.1-flash-lite"]
        response_text = ""
        for m in models_to_try:
            try:
                res = client.models.generate_content(model=m, contents=prompt)
                response_text = res.text
                break
            except Exception:
                continue

        if not response_text:
            response_text = "⚠️ Hệ thống đang bận, vui lòng thử lại sau giây lát."

        await sender.send_message(response_text)
    except Exception as e:
        logger.error(f"Lỗi tạo bài toán: {e}")
        await sender.send_message("❌ Có lỗi xảy ra khi tạo bài học toán.")

async def handle_ask_question(chat_id: int, question: str):
    """Khi user hỏi bất kỳ câu hỏi nào: Trả lời như một senior engineer, đi thẳng vào đáp án."""
    sender = TelegramSender(bot_token=TELEGRAM_BOT_TOKEN, chat_id=str(chat_id))
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
    Người dùng hỏi: "{question}"

    QUY TẮC TRẢ LỜI CỦA SENIOR ENGINEER:
    - Đi thẳng vào trọng tâm câu trả lời ngay dòng đầu tiên.
    - KHÔNG chào hỏi khách sáo, KHÔNG khen ngợi câu hỏi ("Đây là một câu hỏi rất hay..."), KHÔNG kết luận đạo lý.
    - CẤM các từ sáo rỗng: "đột phá", "then chốt", "hãy tưởng tượng", "không thể phủ nhận", "kỷ nguyên AI".
    - Giải thích bản chất kỹ thuật, kèm ví dụ thực tế hoặc lệnh code nếu có.
    - Định dạng dùng HTML Telegram (<b>, <code>, <i>). Ngắn gọn, không viết tràn lan.
    """
    try:
        models_to_try = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.1-flash-lite"]
        response_text = ""
        for m in models_to_try:
            try:
                res = client.models.generate_content(model=m, contents=prompt)
                response_text = res.text
                break
            except Exception:
                continue

        if not response_text:
            response_text = "Hệ thống đang bận, vui lòng thử lại sau."
        await sender.send_message(response_text)
    except Exception as e:
        logger.error(f"Lỗi trả lời câu hỏi: {e}")
        await sender.send_message("❌ Có lỗi xảy ra khi xử lý câu hỏi.")

async def daily_scheduler_loop():
    """Chạy ngầm để tự động phát bản tin mỗi ngày lúc 07:00 AM VN song song với việc lắng nghe lệnh 24/7."""
    logger.info("⏰ Background Daily Scheduler đã kích hoạt (chờ mốc 07:00 AM VN mỗi ngày)...")
    while True:
        now = datetime.now(VN_TZ)
        target = now.replace(hour=7, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        wait_seconds = (target - now).total_seconds()
        logger.info(f"⏳ Bản tin tự động tiếp theo sẽ gửi sau {wait_seconds/3600:.2f} giờ ({target.strftime('%Y-%m-%d %H:%M:%S')})")

        await asyncio.sleep(wait_seconds)

        logger.info("🔔 Đã đến 07:00 AM VN! Tự động kích hoạt chu trình gửi bản tin ngày...")
        try:
            await run_pipeline()
        except Exception as e:
            logger.error(f"Lỗi khi chạy scheduled pipeline: {e}")

        await asyncio.sleep(60)

async def start_polling():
    """Lắng nghe tin nhắn từ Telegram bằng cơ chế Long Polling siêu nhẹ (không tốn tài nguyên)."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ Chưa cấu hình TELEGRAM_BOT_TOKEN trong .env!")
        return

    logger.info("🤖 Bot đang chạy ở chế độ Lắng nghe Tương tác 2 Chiều 24/7 (Polling Mode)...")
    logger.info("👉 Hãy mở Telegram và nhắn lệnh /read, /ai, /data, /kinhte, /xahoi, /math hoặc bất kỳ câu hỏi nào!")

    offset = 0
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"

    async with httpx.AsyncClient(timeout=35.0) as client:
        while True:
            try:
                res = await client.get(url, params={"offset": offset, "timeout": 20})
                if res.status_code == 200:
                    data = res.json()
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        message = update.get("message", {})
                        chat_id = message.get("chat", {}).get("id")
                        text = message.get("text", "").strip()

                        if not chat_id or not text:
                            continue

                        logger.info(f"📩 Nhận tin nhắn từ {chat_id}: {text}")
                        cmd = text.split()[0].lower()

                        if cmd in ["/start", "/help"]:
                            welcome_msg = (
                                "👋 <b>Chào mừng bạn đến với Bot Điểm Tin Đa Lĩnh Vực 24/7!</b>\n\n"
                                "Bot luôn sẵn sàng phục vụ bạn bất cứ lúc nào. Bạn có thể dùng các lệnh:\n"
                                "• <code>/read</code>: Điểm tin đầy đủ 7 lĩnh vực (Kinh tế, Xã hội, AI, BA, DA, DS, DE)\n"
                                "• <code>/ai</code>: Điểm tin riêng nhóm AI & Paper mới nhất\n"
                                "• <code>/data</code>: Điểm tin nhóm Dữ liệu (BA, DA, DS, DE)\n"
                                "• <code>/kinhte</code>: Điểm tin chuyên mục Kinh tế\n"
                                "• <code>/xahoi</code>: Điểm tin chuyên mục Xã hội\n"
                                "• <code>/math</code>: Bài học trực giác Toán THPT kết nối AI\n"
                                "• <code>/now</code>: Kích hoạt ngay chu trình phát tin tự động\n\n"
                                "👉 <b>Hoặc gõ trực tiếp bất kỳ câu hỏi nào</b> để nhận câu trả lời phân tích thực chiến từ kỹ sư senior!"
                            )
                            sender = TelegramSender(bot_token=TELEGRAM_BOT_TOKEN, chat_id=str(chat_id))
                            asyncio.create_task(sender.send_message(welcome_msg))
                        elif cmd in ["/read", "/baidoc", "/all"]:
                            asyncio.create_task(handle_read_command(chat_id))
                        elif cmd in ["/ai"]:
                            asyncio.create_task(handle_category_command(chat_id, ["AI"], "AI & Trí Tuệ Nhân Tạo"))
                        elif cmd in ["/data"]:
                            asyncio.create_task(handle_category_command(chat_id, ["BA", "DA", "DS", "DE"], "Data (BA, DA, DS, DE)"))
                        elif cmd in ["/kinhte", "/kt"]:
                            asyncio.create_task(handle_category_command(chat_id, ["Kinh tế"], "Kinh Tế"))
                        elif cmd in ["/xahoi", "/xh"]:
                            asyncio.create_task(handle_category_command(chat_id, ["Xã hội"], "Xã Hội"))
                        elif cmd in ["/ba"]:
                            asyncio.create_task(handle_category_command(chat_id, ["BA"], "Business Analyst"))
                        elif cmd in ["/da"]:
                            asyncio.create_task(handle_category_command(chat_id, ["DA"], "Data Analyst"))
                        elif cmd in ["/ds"]:
                            asyncio.create_task(handle_category_command(chat_id, ["DS"], "Data Scientist"))
                        elif cmd in ["/de"]:
                            asyncio.create_task(handle_category_command(chat_id, ["DE"], "Data Engineer"))
                        elif cmd in ["/now", "/daily"]:
                            sender = TelegramSender(bot_token=TELEGRAM_BOT_TOKEN, chat_id=str(chat_id))
                            asyncio.create_task(sender.send_message("🚀 <i>Đang kích hoạt chu trình phát bản tin chính thức...</i>"))
                            asyncio.create_task(run_pipeline())
                        elif cmd in ["/math", "/toan"]:
                            asyncio.create_task(handle_math_command(chat_id))
                        else:
                            asyncio.create_task(handle_ask_question(chat_id, text))

            except httpx.ReadTimeout:
                continue
            except Exception as e:
                logger.error(f"Lỗi polling: {e}")
                await asyncio.sleep(3)

async def main():
    await setup_bot_commands(TELEGRAM_BOT_TOKEN)
    await asyncio.gather(
        start_polling(),
        daily_scheduler_loop()
    )

if __name__ == "__main__":
    asyncio.run(main())
