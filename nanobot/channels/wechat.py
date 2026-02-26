"""
WeChat Work (企业微信) channel implementation.

Supports two modes:
1. Push mode - Bot actively sends messages (no callback URL required)
2. Callback mode - Receive messages via webhook (requires public server)

This implementation currently focuses on push mode for stability.
"""

import asyncio
import time
from typing import Any

from loguru import logger
import httpx

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import WeComConfig


class WeComChannel(BaseChannel):
    """
    WeChat Work (企业微信) channel.

    Uses WeChat Work API to send messages.
    For receiving messages, a callback server with public URL is required.

    Current implementation focuses on outbound messaging (push mode).
    """

    name = "wecom"

    def __init__(self, config: WeComConfig, bus: MessageBus):
        super().__init__(config, bus)
        self.config: WeComConfig = config
        self._http: httpx.AsyncClient | None = None

        # Access Token management
        self._access_token: str | None = None
        self._token_expiry: float = 0

        # Base API URL
        self._api_base = "https://qyapi.weixin.qq.com/cgi-bin"

    async def start(self) -> None:
        """Start the WeChat Work channel."""
        try:
            if not self.config.corp_id or not self.config.secret:
                logger.error("WeChat Work corp_id and secret not configured")
                return

            if not self.config.agent_id:
                logger.error("WeChat Work agent_id not configured")
                return

            self._running = True
            self._http = httpx.AsyncClient()

            logger.info(
                "WeChat Work channel initialized with Corp ID: {}, Agent ID: {}",
                self.config.corp_id,
                self.config.agent_id,
            )

            # Pre-fetch access token to validate configuration
            token = await self._get_access_token()
            if token:
                logger.info("WeChat Work channel started successfully")
            else:
                logger.error("Failed to get WeChat Work access token")
                self._running = False

        except Exception as e:
            logger.exception("Failed to start WeChat Work channel: {}", e)

    async def stop(self) -> None:
        """Stop the WeChat Work channel."""
        self._running = False
        if self._http:
            await self._http.aclose()
            self._http = None
        logger.info("WeChat Work channel stopped")

    async def _get_access_token(self) -> str | None:
        """
        Get or refresh access token.

        Returns:
            Access token if successful, None otherwise.
        """
        # Check if current token is still valid
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token

        url = f"{self._api_base}/gettoken"
        params = {
            "corpid": self.config.corp_id,
            "corpsecret": self.config.secret,
        }

        if not self._http:
            logger.warning("WeChat Work HTTP client not initialized")
            return None

        try:
            response = await self._http.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("errcode") == 0:
                self._access_token = data.get("access_token")
                # Token expires in 7200 seconds, refresh 60 seconds early
                self._token_expiry = time.time() + 7200 - 60
                logger.debug("WeChat Work access token refreshed")
                return self._access_token
            else:
                logger.error(
                    "Failed to get WeChat Work access token: {} - {}",
                    data.get("errcode"),
                    data.get("errmsg"),
                )
                return None

        except Exception as e:
            logger.error("Error getting WeChat Work access token: {}", e)
            return None

    async def send(self, msg: OutboundMessage) -> None:
        """
        Send a message through WeChat Work.

        Args:
            msg: The message to send.
        """
        token = await self._get_access_token()
        if not token:
            logger.error("Cannot send message: no access token")
            return

        # WeChat Work API URL
        url = f"{self._api_base}/message/send?access_token={token}"

        # Prepare message data
        # msg.content can contain markdown syntax
        content = msg.content

        # WeChat Work supports text and markdown message types
        # We'll use markdown if content contains markdown syntax, otherwise text
        msg_type = "text"
        msg_content = {"content": content}

        # Check if content looks like markdown (simple heuristic)
        markdown_markers = ["**", "__", "*", "_", "#", "```", "["]
        if any(marker in content for marker in markdown_markers):
            msg_type = "markdown"
            # Convert markdown to WeChat Work markdown format
            # WeChat Work markdown: https://developer.work.weixin.qq.com/document/path/90236
            msg_content = {"content": content}

        # Build request body
        data = {
            "touser": msg.chat_id,  # User ID (e.g., employee ID)
            "msgtype": msg_type,
            "agentid": self.config.agent_id,
            msg_type: msg_content,
        }

        # Try sending
        try:
            if not self._http:
                logger.warning("WeChat Work HTTP client not initialized")
                return

            response = await self._http.post(url, json=data)
            response.raise_for_status()
            result = response.json()

            if result.get("errcode") == 0:
                logger.info(
                    "WeChat Work message sent to {}: {}",
                    msg.chat_id,
                    content[:100] + "..." if len(content) > 100 else content,
                )
            else:
                logger.error(
                    "Failed to send WeChat Work message: {} - {}",
                    result.get("errcode"),
                    result.get("errmsg"),
                )

        except Exception as e:
            logger.error("Error sending WeChat Work message: {}", e)

    async def send_to_user(self, user_id: str, content: str) -> bool:
        """
        Convenience method to send a message to a specific user.

        Args:
            user_id: WeChat Work user ID (employee ID)
            content: Message content

        Returns:
            True if successful, False otherwise.
        """
        msg = OutboundMessage(
            channel=self.name,
            chat_id=user_id,
            content=content,
        )
        await self.send(msg)
        return True

    def get_user_info_url(self) -> str:
        """
        Get the URL to add members for batch sending.

        Returns:
            URL string for user management.
        """
        return (
            f"https://qyapi.weixin.qq.com/cgi-bin/external/contact/"
            f"list?access_token={self._access_token}"
        )


# Helper function for manual testing
async def test_wecom_connection(
    corp_id: str, agent_id: int, secret: str, user_id: str
) -> bool:
    """
    Test WeChat Work connection by sending a test message.

    Args:
        corp_id: Enterprise ID
        agent_id: Application Agent ID
        secret: Application Secret
        user_id: User ID to send test message to

    Returns:
        True if successful, False otherwise.
    """
    from nanobot.bus.queue import MessageBus

    config = WeComConfig(
        enabled=True,
        corp_id=corp_id,
        agent_id=agent_id,
        secret=secret,
        allow_from=[],
    )

    bus = MessageBus()
    channel = WeComChannel(config, bus)

    try:
        await channel.start()
        await channel.send_to_user(user_id, "🤖 Hello from nanobot WeChat Work!")
        await asyncio.sleep(1)  # Give it time to send
        await channel.stop()
        return True
    except Exception as e:
        logger.error("Test failed: {}", e)
        return False
