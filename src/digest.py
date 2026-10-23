import os
import logging
from google import genai
from typing import Optional

logger = logging.getLogger(__name__)

class DigestGenerator:
    """Biên tập viên AI: Lọc 100% tin rác, dịch tiếng Việt tự nhiên và soạn bài học Toán THPT."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def generate(self, raw_crawled_data: str) -> str:
        """Tạo bản tin bằng Gemini 2.5 Flash, có cơ chế fallback nếu chưa có API key."""
        if not self.api_key:
            logger.warning("⚠️ Chưa cấu hình GEMINI_API_KEY. Sử dụng bản tin mẫu (Dry-run mode).")
            return self._mock_digest()

        logger.info("🧠 Đang gọi Gemini 2.5 Flash để lọc nhiễu và biên tập bản tin...")
        client = genai.Client(api_key=self.api_key)

        prompt = f"""
Bạn là một kỹ sư phần mềm thực dụng. Hãy đọc dữ liệu thô dưới đây và viết một bản tin vắn tắt, ĐI THẲNG VÀO NỘI DUNG CHÍNH, viết tự nhiên như người thật nhắn cho đồng nghiệp, TUYỆT ĐỐI KHÔNG CÓ GIỌNG VĂN AI SLOP.

DỮ LIỆU ĐẦU VÀO:
{raw_crawled_data}

QUY TẮC BẮT BUỘC ĐỂ DIỆT VĂN PHONG AI:
1. DANH SÁCH TỪ BỊ CẤM (TUYỆT ĐỐI KHÔNG DÙNG):
   - "đột phá", "cách mạng", "bước ngoặt", "then chốt", "quan trọng", "hãy tưởng tượng", "hãy cùng khám phá", "kỷ nguyên số", "vũ khí bí mật", "không thể phủ nhận".
2. CÁCH VIẾT:
   - Không mở bài chào hỏi dài dòng, không kết bài tổng kết đạo lý.
   - Viết câu ngắn, chắc, trần thuật sự thật kỹ thuật (Ground Truth).
   - Giải thích bản chất thay vì dùng tính từ khen ngợi.

CẤU TRÚC BẢN TIN (Dùng HTML Telegram: <b>, <code>, <a>, <tg-spoiler>):

⚡ <b>TIÊU ĐIỂM AI HÔM NAY</b>
• <b>Công nghệ:</b> [Tên mô hình/paper + Link nếu có]
• <b>Bản chất:</b> [Giải quyết đúng vấn đề gì, cơ chế ngắn gọn trong 1-2 câu]
• <b>Áp dụng:</b> [Lệnh terminal, config cụ thể hoặc cách dùng thực tế trong 1 dòng]

📐 <b>TOÁN THPT & THỰC TẾ AI</b>
• <b>Khái niệm:</b> [Tên khái niệm lớp 10, 11 hoặc 12]
• <b>Bản chất cốt lõi:</b> [Ý nghĩa hình học/thực tế trần trụi, 1-2 câu]
• <b>Ứng dụng trong AI:</b> [Thuật toán AI dùng nó vào đúng việc gì, không nói chung chung]
• <b>Ví dụ nhanh:</b> [1 ví dụ số hoặc tình huống cụ thể]
"""

        models_to_try = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.1-flash-lite"]
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                return response.text
            except Exception as e:
                logger.warning(f"Thử model {model_name} không thành công: {e}")

        logger.error("Tất cả các model Gemini đều gặp lỗi, chuyển sang bản tin dự phòng.")
        return self._mock_digest()

    def _mock_digest(self) -> str:
        """Bản tin mẫu chất lượng cao khi chưa có API key để test toàn bộ pipeline."""
        return """🌅 <b>BẢN TIN KHỞI ĐỘNG TRÍ TUỆ — 07:00 AM</b>

🤖 <b>1. BẢN CHẤT CÔNG NGHỆ AI HÔM NAY</b>
• <b>Đột phá thực tế:</b> <i>Flash-Decoding cho Mô hình Ngôn ngữ Nhỏ</i>. Kỹ thuật mới tối ưu hóa việc phân bổ bộ nhớ trong quá trình giải mã attention, giúp giảm 60% độ trễ sinh từ đầu tiên (Time to First Token).
• <b>Tại sao bạn nên quan tâm?</b> Nếu bạn chạy mô hình cục bộ (Local LLM) trên máy tính xách tay hoặc VPS giá rẻ, phản hồi sẽ mượt hơn đáng kể mà không cần nâng cấp GPU.
• <b>Bài học áp dụng ngay:</b> Khi dùng vLLM hoặc Ollama, hãy bật cờ flash-decoding để tận dụng tối đa băng thông bộ nhớ.

📐 <b>2. TOÁN HỌC & BẢN CHẤT TRỰC GIÁC (Toán THPT kết nối AI)</b>
• <b>Khái niệm:</b> <i>Tích vô hướng của 2 Vectơ (Hình học Lớp 10)</i>
• <b>Bản chất bằng mắt:</b> Hai mũi tên chỉ cùng hướng thì tích vô hướng cực đại; vuông góc (không liên quan) thì bằng 0; ngược hướng thì nhận giá trị âm.
• <b>Thuật toán AI dùng nó thế nào?</b> Cơ chế Self-Attention trong ChatGPT biến mọi từ ngữ thành các vector hàng ngàn chiều. Tích vô hướng giữa hai từ đo mức độ liên quan ngữ nghĩa giữa chúng.
• <b>Câu hỏi phản xạ 30 giây:</b> Nếu hai vector ngữ nghĩa có tích vô hướng bằng 0, nghĩa là hai khái niệm đó như thế nào với nhau?
👉 <tg-spoiler>Đáp án: Hoàn toàn không liên quan đến nhau (độc lập trực giao).</tg-spoiler>"""
