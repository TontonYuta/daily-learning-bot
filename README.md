# 🌅 Daily Automated Learning Bot (AI & Toán học Trực giác)

Bot tự động hóa thu thập kiến thức, lọc tin rác, dịch tiếng Việt tự nhiên và gửi bản tin học tập mỗi ngày lúc 07:00 sáng qua Telegram.

## 🛠️ Công nghệ & Kiến trúc
- **Tự động hóa Web:** [Playwright](https://playwright.dev/) (Headless Chromium) trích xuất dữ liệu bài viết mới nhất từ [Hugging Face Papers](https://huggingface.co/papers).
- **Trí tuệ nhân tạo:** Google Gemini 2.5 Flash lọc 100% tin rác, chắt lọc bài học thực chiến và sinh bài toán THPT bản chất trực giác.
- **Phân phối:** Telegram Bot API (định dạng HTML, spoiler đáp án, đường dẫn bài báo).
- **Lên lịch Miễn phí:** GitHub Actions (chạy đúng 07:00 AM giờ VN và tự tắt, 0 VNĐ vĩnh viễn).

---

## 🚀 Khởi chạy và Kiểm thử cục bộ (Local)

### 1. Cài đặt môi trường
```bash
git clone <repo-url>
cd daily-learning-bot

# Cài đặt thư viện với uv
uv sync
uv run playwright install chromium
```

### 2. Cấu hình biến môi trường
Tạo tệp `.env` từ `.env.example`:
```bash
cp .env.example .env
```
Điền các giá trị:
- `GEMINI_API_KEY`: Lấy miễn phí tại [Google AI Studio](https://aistudio.google.com/)
- `TELEGRAM_BOT_TOKEN`: Lấy từ `@BotFather`
- `TELEGRAM_CHAT_ID`: Lấy từ `@userinfobot`

### 3. Chạy kiểm thử tự động
```bash
uv run pytest
```

### 4. Chạy pipeline thực tế
```bash
uv run python -m src.main
```
*(Nếu chưa cấu hình Telegram, bot sẽ chạy ở chế độ Dry-Run và in trực tiếp nội dung bản tin ra terminal).*

---

## ⏰ Tự động hóa với GitHub Actions

1. Đẩy mã nguồn lên GitHub (chế độ **Private**).
2. Vào **Settings > Secrets and variables > Actions** và thêm 3 Secrets:
   - `GEMINI_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. Đúng 07:00 sáng mỗi ngày (00:00 UTC), GitHub Actions sẽ tự động kích hoạt workflow `.github/workflows/daily.yml`.
