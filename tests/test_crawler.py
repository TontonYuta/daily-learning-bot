import pytest
from src.crawler import PlaywrightAICrawler, MultiCategoryNewsCrawler, clean_html, parse_rss_feed
from src.digest import DigestGenerator
from src.telegram_sender import TelegramSender

@pytest.mark.asyncio
async def test_playwright_crawler_initialization_and_formatting():
    crawler = PlaywrightAICrawler(headless=True)
    sample_papers = [
        {
            "title": "DeepSeek-V3 Technical Report",
            "url": "https://huggingface.co/papers/2412.19437",
            "description": "A strong Mixture-of-Experts language model.",
            "upvotes": "512"
        }
    ]
    formatted = crawler.format_for_llm(sample_papers)
    assert "TOP AI PAPERS EXTRACTED TODAY" in formatted
    assert "DeepSeek-V3" in formatted
    assert "512" in formatted

@pytest.mark.asyncio
async def test_playwright_browser_launch_and_scrape():
    """Verify Playwright headless browser launches and extracts from live or fallback source."""
    crawler = PlaywrightAICrawler(headless=True, timeout_ms=15000)
    papers = await crawler.crawl_huggingface_papers(max_items=2)
    assert isinstance(papers, list)
    if len(papers) > 0:
        assert "title" in papers[0]
        assert "url" in papers[0]

def test_clean_html_and_parse_rss():
    raw_html = "<p>Tin tức <b>kinh tế</b> <a href='#'>chi tiết</a></p>"
    assert clean_html(raw_html) == "Tin tức kinh tế chi tiết"

    sample_rss = b"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <item>
                <title>Kinh te VN tang truong</title>
                <link>https://vnexpress.net/kinh-te</link>
                <description>&lt;b&gt;Mo ta ngan&lt;/b&gt;</description>
            </item>
        </channel>
    </rss>"""
    items = parse_rss_feed(sample_rss, limit=1, origin="VN")
    assert len(items) == 1
    assert items[0]["title"] == "Kinh te VN tang truong"
    assert items[0]["url"] == "https://vnexpress.net/kinh-te"
    assert items[0]["origin"] == "VN"

@pytest.mark.asyncio
async def test_multi_category_crawler_formatting():
    crawler = MultiCategoryNewsCrawler()
    sample_data = {
        "Kinh tế": [{"title": "Kinh tế tăng trưởng", "url": "https://example.com/kt", "origin": "VN", "description": "Số liệu tích cực"}],
        "AI": [{"title": "DeepSeek R1", "url": "https://example.com/ai", "origin": "Quốc tế", "description": "Mô hình reasoning"}]
    }
    formatted = crawler.format_for_llm(sample_data)
    assert "BẢN TIN ĐA LĨNH VỰC" in formatted
    assert "KINH TẾ" in formatted
    assert "AI" in formatted
    assert "https://example.com/kt" in formatted

def test_digest_generator_mock_mode():
    generator = DigestGenerator(api_key=None)
    digest = generator.generate("Sample news input")
    assert "ĐIỂM TIN ĐA LĨNH VỰC" in digest
    assert "KINH TẾ" in digest
    assert "XÃ HỘI" in digest
    assert "AI" in digest
    assert "BA" in digest
    assert "DA" in digest
    assert "DS" in digest
    assert "DE" in digest
    assert "<a href=" in digest

@pytest.mark.asyncio
async def test_telegram_sender_dry_run():
    sender = TelegramSender(bot_token=None, chat_id=None)
    success = await sender.send_message("<b>Test message</b>")
    assert success is True
