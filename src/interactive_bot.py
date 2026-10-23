import asyncio
import logging
import os
import httpx
from dotenv import load_dotenv

from src.crawler import PlaywrightAICrawler
from src.digest import DigestGenerator
from src.telegram_sender import TelegramSender
from google import genai

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("InteractiveBot")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

async def handle_read_command(chat_id: int):
    """Khi user gõ /read hoặc /baidoc: Cào dữ liệu mới nhất và sinh bài đọc ngay lập tức."""
    sender = TelegramSender(bot_token=TELEGRAM_BOT_TOKEN, chat_id=str(chat_id))
    await sender.send_message("⏳ <i>Đang cào dữ liệu mới nhất từ Hugging Face và biên soạn bài đọc cho bạn... Vui lòng đợi trong giây lát!</i>")

    crawler = PlaywrightAICrawler(headless=True)
    papers = await crawler.crawl_huggingface_papers(max_items=5)
    formatted_data = crawler.format_for_llm(papers)

    generator = DigestGenerator(api_key=GEMINI_API_KEY)
    digest_html = generator.generate(formatted_data)

    await sender.send_message(digest_html)

async def handle_math_command(chat_id: int):
    """Khi user gõ /math: Sinh riêng 1 bài toán THPT kết nối với thực tế/AI."""
    sender = TelegramSender(bot_token=TELEGRAM_BOT_TOKEN, chat_id=str(chat_id))
    await sender.send_message("📐 <i>Đang biên soạn 1 bài học Toán học trực giác cho bạn...</i>")

    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = """
    Bạn là một nhà sư phạm toán học xuất sắc. Hãy chọn ngẫu nhiên 1 chủ đề toán THPT (Lớp 10, 11 hoặc 12: Đạo hàm, Tích phân, Vectơ, Xác suất Bayes, Ma trận, Nhị thức Newton...).
    Biên soạn một bài học ngắn bằng tiếng Việt chuẩn mực theo định dạng HTML của Telegram (dùng <b>, <i>, <code>, <tg-spoiler>):

    📐 <b>BÀI HỌC TOÁN HỌC TRỰC GIÁC (TOÁN THPT & AI)</b>
    • <b>Khái niệm:</b> [Tên khái niệm]
    • <b>Bản chất bằng mắt (Intuition):</b> Giải thích bằng hình tượng đời sống thực tế, không đọc vẹt công thức.
    • <b>Ứng dụng trong AI / Công nghệ:</b> Thuật toán máy học hiện đại dùng khái niệm này ở đâu và như thế nào?
    • <b>Thử thách phản xạ tư duy:</b> 1 câu hỏi nhỏ kích thích người đọc.
    👉 <tg-spoiler>Đáp án: [Giải thích]</tg-spoiler>
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
    """Khi user hỏi bất kỳ câu hỏi nào: Giải thích theo phong cách trực giác, súc tích."""
    sender = TelegramSender(bot_token=TELEGRAM_BOT_TOKEN, chat_id=str(chat_id))
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
    Bạn là một kỹ sư AI kiêm chuyên gia sư phạm. Người dùng hỏi bạn:
    "{question}"

    YÊU CẦU TRẢ LỜI:
    - Bằng tiếng Việt tự nhiên, súc tích, đi thẳng vào bản chất vấn đề.
    - Dùng ví dụ trực quan hoặc hình tượng hóa để người đọc dễ hiểu nhất.
    - Định dạng dùng HTML Telegram (<b>, <i>, <code>).
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

async def start_polling():
    """Lắng nghe tin nhắn từ Telegram bằng cơ chế Long Polling siêu nhẹ (không tốn tài nguyên)."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ Chưa cấu hình TELEGRAM_BOT_TOKEN trong .env!")
        return

    logger.info("🤖 Bot đang chạy ở chế độ Lắng nghe Tương tác 2 Chiều (Polling Mode)...")
    logger.info("👉 Hãy mở Telegram và nhắn lệnh /read, /math hoặc bất kỳ câu hỏi nào!")

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

                        if text in ["/start", "/help"]:
                            welcome_msg = (
                                "👋 <b>Chào mừng bạn đến với Bot Trí Tuệ Cá Nhân!</b>\n\n"
                                "Bạn có thể chủ động nhờ bot ra bài bất kỳ lúc nào bằng các lệnh sau:\n"
                                "• <code>/read</code> hoặc <code>/baidoc</code>: Cào tin tức AI mới nhất và tạo bài đọc ngay.\n"
                                "• <code>/math</code>: Tạo ngay 1 bài học trực giác Toán THPT kết nối AI.\n"
                                "• <b>Hoặc gõ trực tiếp bất kỳ câu hỏi nào</b> (ví dụ: <i>Giải thích Attention là gì</i>) để bot giải thích ngay lập tức!"
                            )
                            sender = TelegramSender(bot_token=TELEGRAM_BOT_TOKEN, chat_id=str(chat_id))
                            await sender.send_message(welcome_msg)
                        elif text in ["/read", "/baidoc"]:
                            await handle_read_command(chat_id)
                        elif text in ["/math", "/toan"]:
                            await handle_math_command(chat_id)
                        else:
                            await handle_ask_question(chat_id, text)

            except httpx.ReadTimeout:
                continue
            except Exception as e:
                logger.error(f"Lỗi polling: {e}")
                await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(start_polling())
