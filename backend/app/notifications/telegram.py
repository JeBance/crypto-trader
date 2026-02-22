"""Telegram notification plugin."""

import logging

import aiohttp

from app.plugins.base import NotifierPlugin

logger = logging.getLogger(__name__)


class TelegramNotifier(NotifierPlugin):
    """
    Telegram bot notification plugin.
    
    Sends trading notifications to Telegram chat via Bot API.
    
    Configuration:
    - bot_token: Telegram bot token from @BotFather
    - chat_id: Target chat ID (user or group)
    - parse_mode: Message parse mode (default: HTML)
    
    Example:
        >>> notifier = TelegramNotifier(
        ...     bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        ...     chat_id="123456789"
        ... )
        >>> await notifier.initialize()
        >>> await notifier.send("Hello from Crypto Trader!")
    """
    
    name = "telegram"
    version = "1.0.0"
    description = "Telegram bot notifications"
    
    # Telegram Bot API endpoint
    API_URL = "https://api.telegram.org/bot"
    
    def __init__(
        self,
        bot_token: str = "",
        chat_id: str = "",
        parse_mode: str = "HTML",
        config: dict | None = None,
    ):
        merged_config = config or {}
        merged_config.setdefault("bot_token", bot_token)
        merged_config.setdefault("chat_id", chat_id)
        merged_config.setdefault("parse_mode", parse_mode)
        
        super().__init__(merged_config)
        
        self.bot_token = merged_config["bot_token"]
        self.chat_id = merged_config["chat_id"]
        self.parse_mode = merged_config["parse_mode"]
        
        self._session: aiohttp.ClientSession | None = None
    
    @property
    def is_configured(self) -> bool:
        """Check if notifier is properly configured."""
        return bool(self.bot_token and self.chat_id)
    
    async def initialize(self) -> None:
        """Initialize Telegram bot session."""
        if not self.is_configured:
            logger.warning("Telegram notifier not configured (missing bot_token or chat_id)")
            self._initialized = False
            return
        
        logger.info("Initializing Telegram notifier...")
        
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
        )
        
        # Test connection by getting bot info
        try:
            bot_info = await self._request("getMe")
            if bot_info.get("ok"):
                username = bot_info.get("result", {}).get("username", "unknown")
                logger.info(f"Telegram bot connected: @{username}")
                self._initialized = True
            else:
                logger.error(f"Telegram bot auth failed: {bot_info}")
                self._initialized = False
        except Exception as e:
            logger.error(f"Failed to connect Telegram bot: {e}")
            self._initialized = False
    
    async def shutdown(self) -> None:
        """Shutdown Telegram session."""
        logger.info("Shutting down Telegram notifier...")
        
        if self._session:
            await self._session.close()
            self._session = None
        
        self._initialized = False
    
    async def _request(self, method: str, data: dict | None = None) -> dict:
        """
        Make Telegram Bot API request.
        
        Args:
            method: API method name
            data: Request data
            
        Returns:
            API response
        """
        if not self._session:
            raise RuntimeError("Session not initialized")
        
        url = f"{self.API_URL}{self.bot_token}/{method}"
        
        async with self._session.post(url, json=data) as response:
            return await response.json()
    
    async def send(self, message: str, level: str = "info") -> None:
        """
        Send a notification message.
        
        Args:
            message: Message text (supports HTML markup)
            level: Notification level (info, warning, error, success)
        """
        if not self.is_configured or not self._initialized:
            logger.warning(f"Telegram notifier not ready, skipping message: {message[:50]}...")
            return
        
        # Add emoji based on level
        emojis = {
            "info": "📊",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅",
        }
        emoji = emojis.get(level.lower(), "📊")
        
        # Format message with emoji header
        formatted_message = f"{emoji} {message}"
        
        # Truncate if too long (Telegram limit: 4096 chars)
        if len(formatted_message) > 4000:
            formatted_message = formatted_message[:4000] + "\n\n... (truncated)"
        
        try:
            data = {
                "chat_id": self.chat_id,
                "text": formatted_message,
                "parse_mode": self.parse_mode,
            }
            
            response = await self._request("sendMessage", data)
            
            if not response.get("ok"):
                error = response.get("description", "Unknown error")
                logger.error(f"Telegram send failed: {error}")
            else:
                logger.debug(f"Telegram message sent: {message[:50]}...")
                
        except Exception as e:
            logger.error(f"Telegram notification error: {e}")
    
    async def send_photo(self, photo_url: str, caption: str = "") -> None:
        """
        Send a photo with caption.
        
        Args:
            photo_url: URL of the photo
            caption: Photo caption
        """
        if not self.is_configured or not self._initialized:
            return
        
        try:
            data = {
                "chat_id": self.chat_id,
                "photo": photo_url,
                "caption": caption,
                "parse_mode": self.parse_mode,
            }
            
            await self._request("sendPhoto", data)
            
        except Exception as e:
            logger.error(f"Telegram send photo error: {e}")
    
    async def test_connection(self) -> bool:
        """
        Test Telegram connection with a test message.
        
        Returns:
            True if test successful
        """
        test_message = (
            "<b>🔔 Crypto Trader Test</b>\n\n"
            "Telegram notifier is working correctly!\n\n"
            f"<b>Bot:</b> @{self.bot_token.split(':')[0] if ':' in self.bot_token else 'unknown'}\n"
            f"<b>Chat ID:</b> <code>{self.chat_id}</code>"
        )
        
        await self.send(test_message, level="success")
        return True
    
    def get_info(self) -> dict:
        """Get notifier information."""
        return {
            **super().get_info(),
            "chat_id": self.chat_id,
            "configured": str(self.is_configured),
        }
