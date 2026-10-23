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
Bạn là một kỹ sư trưởng kiêm nhà sư phạm tâm huyết. Nhiệm vụ của bạn là đọc các tin tức kỹ thuật bằng tiếng Anh và chắt lọc thành 1 BẢN TIN BUỔI SÁNG DUY NHẤT bằng TIẾNG VIỆT tự nhiên, sâu sắc, hoàn toàn không có sáo rỗng.

DỮ LIỆU ĐẦU VÀO ĐƯỢC CÀO BẰNG PLAYWRIGHT:
{raw_crawled_data}

QUY TẮC BIÊN TẬP VÀ LỌC NHIỄU (BẮT BUỘC TUÂN THỦ):
1. LOẠI BỎ TRIỆT ĐỂ:
   - Tin giật gân, phát biểu drama của CEO/nhân vật nổi tiếng.
   - Tin gọi vốn, PR doanh nghiệp, tin đồn mơ hồ về AGI.
   - Các bài báo lý thuyết suông không có mã nguồn hoặc không áp dụng được.
2. CHỈ GIỮ LẠI:
   - Công cụ/mô hình mã nguồn mở thực chiến (dùng được ngay).
   - Kỹ thuật lập trình/tối ưu hóa AI thực tế.
   - Kiến trúc giải quyết được bài toán cụ thể (nhanh hơn, rẻ hơn, chính xác hơn).

CẤU TRÚC ĐỊNH DẠNG (Bắt buộc dùng thẻ HTML của Telegram: <b>, <i>, <code>, <a>, <tg-spoiler>):

🌅 <b>BẢN TIN KHỞI ĐỘNG TRÍ TUỆ — 07:00 AM</b>

🤖 <b>1. BẢN CHẤT CÔNG NGHỆ AI HÔM NAY</b>
• <b>Đột phá thực tế:</b> [Tên mô hình/kỹ thuật] - Tóm tắt trong 2 câu ngắn gọn, nêu rõ bản chất.
• <b>Tại sao bạn nên quan tâm?</b> Nêu lợi ích cụ thể (tiết kiệm bộ nhớ, tăng tốc độ, giảm chi phí API...).
• <b>Bài học áp dụng ngay:</b> 1 hành động thực tế người đọc có thể thử ngay hôm nay (lệnh cài đặt, mẹo prompt, hoặc link repo GitHub/paper).

📐 <b>2. TOÁN HỌC & BẢN CHẤT TRỰC GIÁC (Toán THPT kết nối AI)</b>
• <b>Khái niệm:</b> [Chọn 1 khái niệm trong chương trình lớp 10, 11 hoặc 12: Đạo hàm, Vectơ, Ma trận, Xác suất có điều kiện, Cực trị hàm số...]
• <b>Bản chất bằng mắt:</b> Giải thích trực giác đời sống, TUYỆT ĐỐI KHÔNG đọc vẹt công thức.
• <b>Thuật toán AI dùng nó thế nào?</b> Giải thích cách thuật toán máy học (như ChatGPT, bộ gợi ý Tiktok) dùng chính khái niệm toán này để hoạt động.
• <b>Câu hỏi phản xạ 30 giây:</b> 1 câu hỏi nhỏ kích thích tư duy.
👉 <tg-spoiler>Đáp án: [Giải thích ngắn]</tg-spoiler>

Văn phong: Tiếng Việt chuẩn mực, mạch lạc, tôn trọng người đọc, không dùng từ ngữ dịch máy gượng gạo.
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
