import pytest
from unittest.mock import patch, AsyncMock
from src.interactive_bot import setup_bot_commands, handle_category_command

@pytest.mark.asyncio
async def test_setup_bot_commands_no_token():
    # Should safely return without error when token is None
    await setup_bot_commands(None)

@pytest.mark.asyncio
async def test_setup_bot_commands_with_mock():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        await setup_bot_commands("test_token")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "setMyCommands" in args[0]
        assert len(kwargs["json"]["commands"]) >= 6

@pytest.mark.asyncio
async def test_handle_category_command_dry_run():
    # Test on-demand category dispatch in dry run mode
    with patch("src.telegram_sender.TelegramSender.send_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        await handle_category_command(12345, ["AI"], "AI & Trí Tuệ Nhân Tạo")
        # Should send 2 messages: progress wait + digest
        assert mock_send.call_count == 2
