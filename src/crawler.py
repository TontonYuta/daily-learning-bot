import asyncio
import logging
from typing import List, Dict, Any
from playwright.async_api import async_playwright, Browser, Page

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

        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page: Page = await context.new_page()

            try:
                url = "https://huggingface.co/papers"
                logger.info(f"🌐 Navigating to {url}...")
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)

                # Wait for paper articles to load
                await page.wait_for_selector("article, div.cursor-pointer", timeout=10000)

                # Query paper elements
                articles = await page.query_selector_all("article")
                logger.info(f"📄 Found {len(articles)} article nodes on page.")

                for idx, article in enumerate(articles[:max_items]):
                    title_elem = await article.query_selector("h3, a.line-clamp-2, a[href^='/papers/']")
                    link_elem = await article.query_selector("a[href^='/papers/']")
                    desc_elem = await article.query_selector("p, div.line-clamp-3")
                    upvote_elem = await article.query_selector("button, div.leading-none")

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
                await context.close()
                await browser.close()

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

if __name__ == "__main__":
    crawler = PlaywrightAICrawler(headless=True)
    results = asyncio.run(crawler.crawl_huggingface_papers(max_items=3))
    print(crawler.format_for_llm(results))
