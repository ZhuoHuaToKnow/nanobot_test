"""MCP client: connects to MCP servers and wraps their tools as native nanobot tools."""

import asyncio
from contextlib import AsyncExitStack
from typing import Any

import httpx
from loguru import logger

from nanobot.agent.tools.base import Tool
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.agent.tools.mcp_cache import MCPCache


class MCPToolWrapper(Tool):
    """Wraps a single MCP server tool as a nanobot Tool."""

    def __init__(self, session, server_name: str, tool_def, tool_timeout: int = 30):
        self._session = session
        self._original_name = tool_def.name
        self._name = f"mcp_{server_name}_{tool_def.name}"
        self._description = tool_def.description or tool_def.name
        self._parameters = tool_def.inputSchema or {"type": "object", "properties": {}}
        self._tool_timeout = tool_timeout

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> dict[str, Any]:
        return self._parameters

    async def execute(self, **kwargs: Any) -> str:
        from mcp import types
        try:
            result = await asyncio.wait_for(
                self._session.call_tool(self._original_name, arguments=kwargs),
                timeout=self._tool_timeout,
            )
        except asyncio.TimeoutError:
            logger.warning("MCP tool '{}' timed out after {}s", self._name, self._tool_timeout)
            return f"(MCP tool call timed out after {self._tool_timeout}s)"
        parts = []
        for block in result.content:
            if isinstance(block, types.TextContent):
                parts.append(block.text)
            else:
                parts.append(str(block))
        return "\n".join(parts) or "(no output)"


class CachedMCPToolWrapper(Tool):
    """MCP tool wrapper loaded from cache (without active session)."""

    def __init__(
        self,
        server_name: str,
        tool_def: dict,
        tool_timeout: int = 30,
        session_getter: callable = None,
    ):
        self._server_name = server_name
        self._original_name = tool_def["original_name"]
        self._name = tool_def["mcp_name"]
        self._description = tool_def["description"]
        self._parameters = tool_def["parameters"]
        self._tool_timeout = tool_timeout
        self._session_getter = session_getter

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> dict[str, Any]:
        return self._parameters

    async def execute(self, **kwargs: Any) -> str:
        if not self._session_getter:
            return "(MCP tool not available: no active session)"

        session = self._session_getter(self._server_name)
        if not session:
            return f"(MCP tool not available: server '{self._server_name}' not connected)"

        from mcp import types
        try:
            result = await asyncio.wait_for(
                session.call_tool(self._original_name, arguments=kwargs),
                timeout=self._tool_timeout,
            )
        except asyncio.TimeoutError:
            logger.warning("MCP tool '{}' timed out after {}s", self._name, self._tool_timeout)
            return f"(MCP tool call timed out after {self._tool_timeout}s)"
        parts = []
        for block in result.content:
            if isinstance(block, types.TextContent):
                parts.append(block.text)
            else:
                parts.append(str(block))
        return "\n".join(parts) or "(no output)"


def _tool_def_to_cache(server_name: str, tool_def) -> dict:
    """Convert MCP tool definition to cache format."""
    return {
        "original_name": tool_def.name,
        "mcp_name": f"mcp_{server_name}_{tool_def.name}",
        "description": tool_def.description or tool_def.name,
        "parameters": tool_def.inputSchema or {"type": "object", "properties": {}},
    }


async def connect_mcp_servers(
    mcp_servers: dict, registry: ToolRegistry, stack: AsyncExitStack
) -> dict[str, Any]:
    """Connect to configured MCP servers and register their tools.

    Returns:
        Dict mapping server names to their sessions for later use.
    """
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    cache = MCPCache()
    cache.load()

    sessions = {}
    config_dict = {name: cfg.model_dump() for name, cfg in mcp_servers.items()}

    for name, cfg in mcp_servers.items():
        try:
            if cfg.command:
                params = StdioServerParameters(
                    command=cfg.command, args=cfg.args, env=cfg.env or None
                )
                read, write = await stack.enter_async_context(stdio_client(params))
            elif cfg.url:
                from mcp.client.streamable_http import streamable_http_client
                # Always provide an explicit httpx client so MCP HTTP transport does not
                # inherit httpx's default 5s timeout and preempt the higher-level tool timeout.
                http_client = await stack.enter_async_context(
                    httpx.AsyncClient(
                        headers=cfg.headers or None,
                        follow_redirects=True,
                        timeout=None,
                    )
                )
                read, write, _ = await stack.enter_async_context(
                    streamable_http_client(cfg.url, http_client=http_client)
                )
            else:
                logger.warning("MCP server '{}': no command or url configured, skipping", name)
                continue

            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()

            tools = await session.list_tools()
            tool_defs = [_tool_def_to_cache(name, t) for t in tools.tools]

            for tool_def in tools.tools:
                wrapper = MCPToolWrapper(session, name, tool_def, tool_timeout=cfg.tool_timeout)
                registry.register(wrapper)
                logger.debug("MCP: registered tool '{}' from server '{}'", wrapper.name, name)

            # Cache the tool definitions
            cache.set(name, config_dict[name], tool_defs)

            sessions[name] = session
            logger.info("MCP server '{}': connected, {} tools registered", name, len(tools.tools))
        except Exception as e:
            logger.error("MCP server '{}': failed to connect: {}", name, e)

    # Save cache after all connections
    cache.save()
    return sessions


async def load_mcp_tools_from_cache(
    mcp_servers: dict, registry: ToolRegistry, session_getter: callable
) -> bool:
    """Load MCP tools from cache without connecting to servers.

    Args:
        mcp_servers: MCP server configurations.
        registry: Tool registry to register tools to.
        session_getter: Callable that takes server_name and returns MCP session.

    Returns:
        True if cache was loaded successfully, False otherwise.
    """
    cache = MCPCache()
    if not cache.load():
        return False

    config_dict = {name: cfg.model_dump() for name, cfg in mcp_servers.items()}
    loaded_count = 0

    for name, cfg in mcp_servers.items():
        cached = cache.get(name, config_dict[name])
        if not cached:
            logger.debug("MCP server '{}': not in cache or config changed", name)
            continue

        for tool_def in cached.tools:
            wrapper = CachedMCPToolWrapper(
                server_name=name,
                tool_def=tool_def,
                tool_timeout=cfg.tool_timeout,
                session_getter=session_getter,
            )
            registry.register(wrapper)
            loaded_count += 1
            logger.debug("MCP: loaded cached tool '{}' from server '{}'", wrapper.name, name)

        logger.info("MCP server '{}': loaded {} tools from cache", name, len(cached.tools))

    return loaded_count > 0
