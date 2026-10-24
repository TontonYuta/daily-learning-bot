# 🌅 Daily Automated Learning Bot (7 Lĩnh vực: Kinh tế, Xã hội, AI, BA, DA, DS, DE)

Bot tự động hóa thu thập kiến thức đa chiều (trong nước & quốc tế), lọc tin rác, tóm tắt siêu ngắn gọn kèm link nguồn bài đọc, phát bản tin định kỳ 07:00 AM và **sẵn sàng phản hồi On-Demand 24/7 khi người dùng gọi bất kỳ lúc nào qua Telegram**.

## 🛠️ 7 Lĩnh vực tin tức & Nguồn thu thập
1. 💼 **Kinh tế**: VnExpress Kinh Doanh, CafeF, The Guardian Business.
2. 🌍 **Xã hội**: VnExpress Thời sự, The Guardian World News.
3. 🤖 **AI (Trí tuệ nhân tạo)**: Hugging Face Daily Papers, TechCrunch AI.
4. 📊 **BA (Business Analyst)**: Hacker News Product Management & Business Analysis.
5. 📈 **DA (Data Analyst)**: Hacker News Analytics & SQL, KDnuggets Data Analytics.
6. 🔬 **DS (Data Scientist)**: KDnuggets Machine Learning, Hacker News Data Science.
7. 🛠️ **DE (Data Engineer)**: Data Engineering Weekly, Hacker News Data Pipeline (dbt, Kafka, Airflow).

---

## 📱 Lệnh gọi Bot On-Demand bất cứ lúc nào trên Telegram
Người dùng có thể mở Telegram và gọi bot bất cứ lúc nào (Menu lệnh tự động tích hợp trên bàn phím Telegram):
- `/read` hoặc `/all`: Cào và điểm tin tức thời đầy đủ cả 7 lĩnh vực (kèm link nguồn).
- `/ai`: Điểm tin chuyên sâu riêng nhóm AI & Papers mới nhất.
- `/data`: Điểm tin nhóm Dữ liệu (BA, DA, DS, DE).
- `/kinhte`: Điểm tin chuyên mục Kinh tế (VN & Quốc tế).
- `/xahoi`: Điểm tin chuyên mục Xã hội (VN & Quốc tế).
- `/math`: Bài học trực giác Toán THPT kết nối thực tế & AI.
- `/now`: Kích hoạt chu trình phát bản tin chính thức ngay lập tức.
- **Hoặc gõ bất kỳ câu hỏi nào**: Trò chuyện và hỏi đáp kỹ thuật trực tiếp với Senior AI Engineer.

---

## 🚀 2 Chế độ Triển khai Vận hành

### Chế độ 1: Bot 24/7 (Vừa tự động phát 07:00 AM, vừa trả lời ngay khi gọi)
Chạy lệnh duy nhất để khởi động toàn bộ hệ thống gồm Polling 24/7 và Background Scheduler:
```bash
uv run python -m src.interactive_bot
```
*Hoặc triển khai Docker 1-click:*
```bash
docker compose up -d
```

### Chế độ 2: Tự động hóa 0 VNĐ không cần máy chủ (Serverless GitHub Actions)
Nếu bạn không muốn treo máy, GitHub Actions sẽ tự động chạy lúc 06:35 - 07:00 AM hàng ngày và tự tắt:
1. Đẩy mã nguồn lên GitHub (chế độ **Private**).
2. Vào **Settings > Secrets and variables > Actions** và thêm 3 Secrets:
   - `GEMINI_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. Đúng sáng mỗi ngày, workflow `.github/workflows/daily.yml` sẽ tự động kích hoạt.

---

## 🧪 Kiểm thử Tự động (Testing)
```bash
uv run pytest
```
Chạy thử nghiệm toàn bộ chu trình cào 7 danh mục ở chế độ Dry-Run:
```bash
uv run python -m src.main
```
