import pytest
from src.crawler import PlaywrightAICrawler
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

def test_digest_generator_mock_mode():
    generator = DigestGenerator(api_key=None)
    digest = generator.generate("Sample AI paper input")
    assert "KHỞI ĐỘNG TRÍ TUỆ" in digest
    assert "AI HÔM NAY" in digest
    assert "TOÁN HỌC" in digest

@pytest.mark.asyncio
async def test_telegram_sender_dry_run():
    sender = TelegramSender(bot_token=None, chat_id=None)
    success = await sender.send_message("<b>Test message</b>")
    assert success is True
