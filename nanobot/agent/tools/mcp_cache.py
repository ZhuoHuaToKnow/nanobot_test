"""MCP tools cache management."""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger


def get_cache_path() -> Path:
    """Get the MCP tools cache file path."""
    from nanobot.utils.helpers import get_data_path
    return get_data_path() / "mcp_tools_cache.json"


def _hash_config(config: dict) -> str:
    """Generate hash from MCP server config for change detection."""
    # Hash relevant config fields
    key_data = {
        "command": config.get("command", ""),
        "args": config.get("args", []),
        "url": config.get("url", ""),
        "headers": config.get("headers", {}),
    }
    return hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()


class MCPCacheEntry:
    """Cached MCP server entry."""

    def __init__(
        self,
        server_name: str,
        config: dict,
        tools: list[dict],
        cached_at: str | None = None,
    ):
        self.server_name = server_name
        self.config = config
        self.tools = tools
        self.cached_at = cached_at or datetime.now().isoformat()
        self.config_hash = _hash_config(config)

    def is_config_changed(self, current_config: dict) -> bool:
        """Check if config has changed."""
        return _hash_config(current_config) != self.config_hash

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            "server_name": self.server_name,
            "config": self.config,
            "tools": self.tools,
            "cached_at": self.cached_at,
            "config_hash": self.config_hash,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MCPCacheEntry":
        """Create from dict."""
        return cls(
            server_name=data["server_name"],
            config=data["config"],
            tools=data["tools"],
            cached_at=data["cached_at"],
        )


class MCPCache:
    """MCP tools cache manager."""

    VERSION = 1

    def __init__(self, cache_path: Path | None = None):
        self.cache_path = cache_path or get_cache_path()
        self._cache: dict[str, MCPCacheEntry] = {}

    def load(self) -> bool:
        """Load cache from disk. Returns True if successful."""
        if not self.cache_path.exists():
            logger.debug("MCP cache not found: {}", self.cache_path)
            return False

        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate version
            if data.get("version") != self.VERSION:
                logger.warning("MCP cache version mismatch, ignoring cache")
                return False

            # Load entries
            for server_name, entry_data in data.get("servers", {}).items():
                self._cache[server_name] = MCPCacheEntry.from_dict(entry_data)

            logger.info("MCP cache loaded: {} servers", len(self._cache))
            return True
        except Exception as e:
            logger.warning("Failed to load MCP cache: {}", e)
            return False

    def save(self) -> None:
        """Save cache to disk."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": self.VERSION,
            "updated_at": datetime.now().isoformat(),
            "servers": {
                name: entry.to_dict() for name, entry in self._cache.items()
            },
        }

        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.debug("MCP cache saved: {}", self.cache_path)

    def get(self, server_name: str, config: dict) -> MCPCacheEntry | None:
        """Get cached entry if config hasn't changed."""
        entry = self._cache.get(server_name)
        if entry and not entry.is_config_changed(config):
            return entry
        return None

    def set(self, server_name: str, config: dict, tools: list[dict]) -> None:
        """Cache tools for a server."""
        self._cache[server_name] = MCPCacheEntry(server_name, config, tools)

    def remove(self, server_name: str) -> None:
        """Remove server from cache."""
        self._cache.pop(server_name, None)

    def clear(self) -> None:
        """Clear all cache."""
        self._cache.clear()

    def get_all_tools(self) -> list[dict]:
        """Get all cached tools in format for registration."""
        all_tools = []
        for entry in self._cache.values():
            all_tools.extend(entry.tools)
        return all_tools

    def __len__(self) -> int:
        return len(self._cache)

    def __contains__(self, server_name: str) -> bool:
        return server_name in self._cache
