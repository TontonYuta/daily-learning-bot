import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Set, Optional

logger = logging.getLogger(__name__)

# Default VN timezone (UTC+7)
VN_TZ = timezone(timedelta(hours=7))

class HistoryManager:
    """Quản lý lịch sử bài báo đã gửi để loại bỏ trùng lặp (Deduplication)."""

    def __init__(self, history_file: Optional[str] = None, max_history_size: int = 300):
        if history_file is None:
            # Lưu mặc định tại thư mục data/ của dự án
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.history_file = os.path.join(project_root, "data", "history.json")
        else:
            self.history_file = os.path.abspath(history_file)

        self.max_history_size = max_history_size
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        """Đảm bảo thư mục lưu trữ và tệp JSON tồn tại."""
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        if not os.path.exists(self.history_file):
            try:
                with open(self.history_file, "w", encoding="utf-8") as f:
                    json.dump({"sent_papers": []}, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.warning(f"Không thể khởi tạo tệp history: {e}")

    def load_history(self) -> List[Dict[str, Any]]:
        """Đọc danh sách các bài viết đã gửi trong quá khứ."""
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("sent_papers", [])
        except Exception as e:
            logger.error(f"Lỗi khi đọc file lịch sử: {e}")
            return []

    def get_seen_urls(self) -> Set[str]:
        """Lấy tập hợp các URL đã được gửi (đã chuẩn hóa)."""
        history = self.load_history()
        seen = set()
        for item in history:
            url = item.get("url", "").strip().rstrip("/")
            if url:
                seen.add(url)
        return seen

    def filter_unseen(self, papers: List[Dict[str, Any]], max_items: int = 5) -> List[Dict[str, Any]]:
        """
        Lọc bỏ các bài báo đã gửi trong quá khứ.
        Nếu tất cả bài báo đều đã gửi (ví dụ ngày cuối tuần không có bài mới),
        sẽ giữ lại các bài mới nhất để tránh gửi tin trống.
        """
        seen_urls = self.get_seen_urls()
        unseen = [p for p in papers if p.get("url", "").strip().rstrip("/") not in seen_urls]

        if unseen:
            logger.info(f"🔍 Đã lọc {len(unseen)} bài báo mới chưa từng gửi (trên tổng số {len(papers)} bài cào được).")
            return unseen[:max_items]

        logger.warning("⚠️ Tất cả các bài báo cào được đều đã từng gửi trước đó. Chọn các bài hàng đầu để không làm rỗng bản tin.")
        return papers[:max_items]

    def save_history(self, newly_sent_papers: List[Dict[str, Any]]) -> None:
        """Ghi nhận các bài báo vừa gửi vào lịch sử và giới hạn kích thước tối đa."""
        if not newly_sent_papers:
            return

        current_history = self.load_history()
        now_str = datetime.now(VN_TZ).isoformat()

        seen_urls = {item.get("url", "").strip().rstrip("/") for item in current_history}

        added_count = 0
        for p in newly_sent_papers:
            norm_url = p.get("url", "").strip().rstrip("/")
            if norm_url and norm_url not in seen_urls:
                current_history.append({
                    "url": norm_url,
                    "title": p.get("title", ""),
                    "sent_at": now_str
                })
                seen_urls.add(norm_url)
                added_count += 1

        # Giới hạn kích thước file, chỉ giữ lại các bài gần nhất
        if len(current_history) > self.max_history_size:
            current_history = current_history[-self.max_history_size:]

        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump({"sent_papers": current_history}, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Đã lưu thành công {added_count} bài báo vào lịch sử.")
        except Exception as e:
            logger.error(f"Lỗi khi ghi tệp lịch sử bài viết: {e}")
