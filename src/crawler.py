import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import httpx
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class PlaywrightAICrawler:
    """Automated crawler using Playwright to extract top daily AI papers and breakthroughs."""

    def __init__(self, headless: bool = True, timeout_ms: int = 30000):
        self.headless = headless
        self.timeout_ms = timeout_ms

    async def crawl_huggingface_papers(self, max_items: int = 5) -> List[Dict[str, Any]]:
        """
        Launches headless browser via Playwright, navigates to Hugging Face Daily Papers,
        and extracts rendered paper titles, upvotes, summaries, and URLs.
        """
        papers: List[Dict[str, Any]] = []
        logger.info("🚀 Launching Playwright browser (Chromium)...")

        try:
            async with async_playwright() as p:
                browser: Optional[Browser] = None
                context: Optional[BrowserContext] = None
                try:
                    browser = await p.chromium.launch(
                        headless=self.headless,
                        args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
                    )
                    context = await browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    )
                    page: Page = await context.new_page()

                    url = "https://huggingface.co/papers"
                    logger.info(f"🌐 Navigating to {url}...")
                    await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)

                    # Wait for paper articles to load
                    await page.wait_for_selector("article, div.cursor-pointer", timeout=10000)

                    # Query paper elements
                    articles = await page.query_selector_all("article")
                    logger.info(f"📄 Found {len(articles)} article nodes on page.")

                    for idx, article in enumerate(articles[:max_items]):
                        title_elem = await article.query_selector("h3") or await article.query_selector("a.line-clamp-2")
                        link_elem = await article.query_selector("h3 a") or await article.query_selector("a[href^='/papers/']")
                        desc_elem = await article.query_selector("p, div.line-clamp-3")
                        upvote_elem = await article.query_selector("button, div.leading-none, a[href*='login']")

                        title = (await title_elem.inner_text()).strip() if title_elem else "N/A"
                        href = await link_elem.get_attribute("href") if link_elem else ""
                        desc = (await desc_elem.inner_text()).strip() if desc_elem else ""
                        upvotes = (await upvote_elem.inner_text()).strip() if upvote_elem else "0"

                        full_url = f"https://huggingface.co{href}" if href.startswith("/") else href

                        papers.append({
                            "title": title,
                            "url": full_url,
                            "description": desc,
                            "upvotes": upvotes
                        })

                    logger.info(f"✅ Successfully extracted {len(papers)} papers using Playwright.")

                except Exception as e:
                    logger.warning(f"⚠️ Playwright direct DOM extraction failed or timed out: {e}")
                    logger.info("🔄 Falling back to HuggingFace REST API...")
                    papers = await self._fallback_api(max_items)

                finally:
                    if context:
                        try:
                            await context.close()
                        except Exception:
                            pass
                    if browser:
                        try:
                            await browser.close()
                        except Exception:
                            pass
        except Exception as outer_e:
            logger.warning(f"⚠️ Playwright browser initialization completely failed: {outer_e}")
            logger.info("🔄 Falling back to HuggingFace REST API...")
            papers = await self._fallback_api(max_items)

        return papers

    async def _fallback_api(self, max_items: int = 5) -> List[Dict[str, Any]]:
        """Fallback method in case network/DOM changes suddenly on Hugging Face."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get("https://huggingface.co/api/daily_papers")
                if res.status_code == 200:
                    raw = res.json()[:max_items]
                    items = []
                    for item in raw:
                        p = item.get("paper", {})
                        items.append({
                            "title": p.get("title", "Untitled"),
                            "url": f"https://huggingface.co/papers/{p.get('id', '')}",
                            "description": p.get("summary", "")[:250],
                            "upvotes": str(p.get("upvotes", 0))
                        })
                    return items
        except Exception as err:
            logger.error(f"Fallback API also failed: {err}")
        return []

    def format_for_llm(self, papers: List[Dict[str, Any]]) -> str:
        """Converts extracted paper data into clean Markdown representation for Gemini LLM."""
        if not papers:
            return "Không có dữ liệu bài báo mới nhất từ web. Hãy biên soạn dựa trên các xu hướng mô hình ngôn ngữ lớn (LLM) và kỹ thuật lập trình AI hữu ích gần đây."

        lines = ["### TOP AI PAPERS EXTRACTED TODAY (VIA PLAYWRIGHT):"]
        for idx, p in enumerate(papers, 1):
            lines.append(f"{idx}. **Tiêu đề:** {p['title']}")
            lines.append(f"   - **Upvotes:** {p['upvotes']}")
            lines.append(f"   - **Mô tả/Tóm tắt:** {p['description']}")
            lines.append(f"   - **Link gốc:** {p['url']}")
        return "\n".join(lines)

def clean_html(raw_html: str) -> str:
    """Loại bỏ các thẻ HTML để trích xuất text thuần túy."""
    if not raw_html:
        return ""
    clean = re.sub(r"<[^>]+>", " ", raw_html)
    return " ".join(clean.split()).strip()

def parse_rss_feed(content: bytes, limit: int = 3, origin: str = "Quốc tế") -> List[Dict[str, Any]]:
    """Phân tích cú pháp RSS 2.0 / Atom feed thành danh sách bài viết chuẩn hóa."""
    items: List[Dict[str, Any]] = []
    try:
        root = ET.fromstring(content)
        # 1. Tìm các node <item> (RSS)
        nodes = root.findall(".//item")
        if not nodes:
            nodes = [e for e in root.iter() if e.tag.endswith("item")]

        if nodes:
            for node in nodes[:limit]:
                t = next((c for c in node if c.tag.endswith("title")), None)
                l = next((c for c in node if c.tag.endswith("link")), None)
                d = next((c for c in node if c.tag.endswith("description")), None)

                title = t.text.strip() if t is not None and t.text else ""
                url = l.text.strip() if l is not None and l.text else ""
                desc = clean_html(d.text) if d is not None and d.text else ""

                if title and url:
                    items.append({
                        "title": title,
                        "url": url,
                        "description": desc[:250],
                        "origin": origin
                    })
            return items

        # 2. Tìm các node <entry> (Atom)
        entries = [e for e in root.iter() if e.tag.endswith("entry")]
        for entry in entries[:limit]:
            t = next((c for c in entry if c.tag.endswith("title")), None)
            l = next((c for c in entry if c.tag.endswith("link")), None)
            s = next((c for c in entry if c.tag.endswith("summary") or c.tag.endswith("content")), None)

            title = t.text.strip() if t is not None and t.text else ""
            url = l.get("href", "") if l is not None else (l.text or "")
            desc = clean_html(s.text) if s is not None and s.text else ""

            if title and url:
                items.append({
                    "title": title,
                    "url": url,
                    "description": desc[:250],
                    "origin": origin
                })
    except Exception as e:
        logger.debug(f"Lỗi phân tích cú pháp feed XML: {e}")
    return items

DEFAULT_FEED_REGISTRY = {
    "Kinh tế": [
        {"name": "VnExpress Kinh Doanh", "origin": "VN", "url": "https://vnexpress.net/rss/kinh-doanh.rss"},
        {"name": "The Guardian Business", "origin": "Quốc tế", "url": "https://www.theguardian.com/business/rss"},
        {"name": "CafeF Quốc tế", "origin": "VN", "url": "https://cafef.vn/tai-chinh-quoc-te.rss"},
    ],
    "Xã hội": [
        {"name": "VnExpress Thời sự", "origin": "VN", "url": "https://vnexpress.net/rss/thoi-su.rss"},
        {"name": "The Guardian World", "origin": "Quốc tế", "url": "https://www.theguardian.com/world/rss"},
    ],
    "AI": [
        {"name": "Hugging Face Daily Papers", "origin": "Quốc tế", "url": "https://huggingface.co/api/daily_papers", "type": "hf_api"},
        {"name": "TechCrunch AI", "origin": "Quốc tế", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    ],
    "BA": [
        {"name": "HN Business Analysis & Product", "origin": "Quốc tế", "url": "https://hnrss.org/newest?q=Business+Analyst+OR+Product+Management"},
    ],
    "DA": [
        {"name": "HN Data Analytics & SQL", "origin": "Quốc tế", "url": "https://hnrss.org/newest?q=Data+Analyst+OR+SQL+OR+PowerBI+OR+Analytics"},
        {"name": "KDnuggets Data Analytics", "origin": "Quốc tế", "url": "https://www.kdnuggets.com/feed"},
    ],
    "DS": [
        {"name": "KDnuggets Data Science & ML", "origin": "Quốc tế", "url": "https://www.kdnuggets.com/feed"},
        {"name": "HN Data Science & ML", "origin": "Quốc tế", "url": "https://hnrss.org/newest?q=Data+Science+OR+Machine+Learning"},
    ],
    "DE": [
        {"name": "Data Engineering Weekly", "origin": "Quốc tế", "url": "https://www.dataengineeringweekly.com/feed"},
        {"name": "HN Data Engineering", "origin": "Quốc tế", "url": "https://hnrss.org/newest?q=Data+Engineering+OR+dbt+OR+Airflow+OR+Kafka"},
    ],
}

class MultiCategoryNewsCrawler:
    """Bộ thu thập tin tức đa danh mục: Kinh tế, Xã hội, AI, BA, DA, DS, DE (Trong nước & Quốc tế)."""

    def __init__(self, feed_registry: Optional[Dict[str, List[Dict[str, str]]]] = None, timeout: float = 8.0):
        self.feed_registry = feed_registry or DEFAULT_FEED_REGISTRY
        self.timeout = timeout

    async def fetch_source(self, client: httpx.AsyncClient, source: Dict[str, str], limit: int = 3) -> List[Dict[str, Any]]:
        """Cào tin tức từ một nguồn đơn lẻ với cơ chế timeout an toàn."""
        url = source["url"]
        origin = source.get("origin", "Quốc tế")
        source_type = source.get("type", "rss")

        try:
            res = await client.get(url)
            if res.status_code != 200:
                logger.warning(f"Nguồn {url} trả về HTTP {res.status_code}")
                return []

            if source_type == "hf_api":
                papers_data = res.json()[:limit]
                items = []
                for p_item in papers_data:
                    p = p_item.get("paper", {})
                    items.append({
                        "title": p.get("title", "Untitled Paper"),
                        "url": f"https://huggingface.co/papers/{p.get('id', '')}",
                        "description": (p.get("summary") or "")[:250],
                        "origin": origin,
                        "upvotes": str(p.get("upvotes", 0))
                    })
                return items
            else:
                return parse_rss_feed(res.content, limit=limit, origin=origin)
        except Exception as e:
            logger.warning(f"Lỗi khi cào từ {url}: {e}")
            return []

    async def crawl_all_categories(self, limit_per_source: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """Thu thập song song bất đồng bộ toàn bộ 7 danh mục tin tức."""
        categorized_results: Dict[str, List[Dict[str, Any]]] = {cat: [] for cat in self.feed_registry}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
            tasks = []
            category_mapping = []

            for category, sources in self.feed_registry.items():
                for src in sources:
                    tasks.append(self.fetch_source(client, src, limit=limit_per_source))
                    category_mapping.append(category)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for category, res in zip(category_mapping, results):
                if isinstance(res, list):
                    categorized_results[category].extend(res)

        return categorized_results

    def format_for_llm(self, categorized_news: Dict[str, List[Dict[str, Any]]]) -> str:
        """Định dạng dữ liệu các danh mục thành Markdown ngắn gọn cho Gemini."""
        sections = ["### BẢN TIN ĐA LĨNH VỰC HÔM NAY (Kinh tế, Xã hội, AI, BA, DA, DS, DE):"]

        for category, items in categorized_news.items():
            sections.append(f"\n#### [{category.upper()}]:")
            if not items:
                sections.append("- (Không có dữ liệu mới từ web)")
                continue

            for idx, item in enumerate(items, 1):
                origin_tag = f"[{item.get('origin', 'Quốc tế')}]"
                sections.append(
                    f"{idx}. {origin_tag} **{item['title']}**\n"
                    f"   - Link: {item['url']}\n"
                    f"   - Tóm tắt: {item.get('description', '')}"
                )

        return "\n".join(sections)

if __name__ == "__main__":
    crawler = PlaywrightAICrawler(headless=True)
    results = asyncio.run(crawler.crawl_huggingface_papers(max_items=3))
    print(crawler.format_for_llm(results))
