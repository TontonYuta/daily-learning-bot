import os
import json
import pytest
from unittest.mock import patch, AsyncMock
from src.history import HistoryManager
from src.crawler import PlaywrightAICrawler

def test_history_manager_filter_and_save(tmp_path):
    history_file = tmp_path / "test_history.json"
    manager = HistoryManager(history_file=str(history_file))

    raw_papers = [
        {"title": "Paper 1", "url": "https://huggingface.co/papers/1111.1111", "upvotes": "10"},
        {"title": "Paper 2", "url": "https://huggingface.co/papers/2222.2222", "upvotes": "20"},
        {"title": "Paper 3", "url": "https://huggingface.co/papers/3333.3333", "upvotes": "30"},
    ]

    # First run: all 3 papers are unseen
    unseen = manager.filter_unseen(raw_papers, max_items=2)
    assert len(unseen) == 2
    assert unseen[0]["title"] == "Paper 1"
    assert unseen[1]["title"] == "Paper 2"

    # Save the first two papers
    manager.save_history(unseen)

    # Second run: Paper 1 & 2 are now seen, only Paper 3 is unseen
    unseen_run2 = manager.filter_unseen(raw_papers, max_items=2)
    assert len(unseen_run2) == 1
    assert unseen_run2[0]["title"] == "Paper 3"

    # Save Paper 3
    manager.save_history(unseen_run2)

    # Third run: all papers are seen. Fallback should return items so digest isn't empty
    unseen_run3 = manager.filter_unseen(raw_papers, max_items=2)
    assert len(unseen_run3) == 2

def test_history_manager_size_limit(tmp_path):
    history_file = tmp_path / "test_history_limit.json"
    manager = HistoryManager(history_file=str(history_file), max_history_size=5)

    papers = [{"title": f"Paper {i}", "url": f"https://huggingface.co/papers/{i}"} for i in range(10)]
    manager.save_history(papers)

    history = manager.load_history()
    assert len(history) == 5
    assert history[-1]["url"] == "https://huggingface.co/papers/9"

@pytest.mark.asyncio
async def test_crawler_launch_failure_fallback():
    """Verify that if Playwright browser launch raises an exception, crawler gracefully uses fallback API."""
    crawler = PlaywrightAICrawler(headless=True)
    with patch("src.crawler.async_playwright") as mock_playwright:
        mock_p = AsyncMock()
        mock_p.chromium.launch.side_effect = Exception("Simulated browser binary missing")
        mock_playwright.return_value.__aenter__.return_value = mock_p

        # Mock the fallback API to verify it gets called
        with patch.object(crawler, "_fallback_api", new_callable=AsyncMock) as mock_fallback:
            mock_fallback.return_value = [{"title": "Fallback Paper", "url": "https://huggingface.co/papers/fallback"}]
            papers = await crawler.crawl_huggingface_papers(max_items=1)
            assert len(papers) == 1
            assert papers[0]["title"] == "Fallback Paper"
            mock_fallback.assert_called_once_with(1)
