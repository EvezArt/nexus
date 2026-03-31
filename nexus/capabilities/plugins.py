"""
Nexus Plugins — hot-loading capability extension system.

Capabilities:
- Dynamic plugin registration at runtime
- Plugin lifecycle management (load/unload/enable/disable)
- Plugin discovery (scan directory for plugins)
- Dependency resolution
- Plugin config and metadata

Usage:
    from nexus.capabilities.plugins import PluginManager
    pm = PluginManager()
    pm.register("my_plugin", MyPluginClass)
    plugin = pm.get("my_plugin")
    result = await plugin.execute("task", data={...})
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List, Type
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


WORKSPACE = Path("/root/.openclaw/workspace")
PLUGIN_DIR = WORKSPACE / "nexus" / "plugins"


class PluginStatus(str, Enum):
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    UNLOADED = "unloaded"


@dataclass
class PluginMeta:
    """Plugin metadata."""
    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    status: PluginStatus = PluginStatus.UNLOADED
    loaded_at: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "capabilities": self.capabilities,
            "dependencies": self.dependencies,
            "status": self.status.value if isinstance(self.status, PluginStatus) else self.status,
            "loaded_at": self.loaded_at,
            "error": self.error,
        }


class BasePlugin(ABC):
    """Base class that all plugins must implement."""

    meta: PluginMeta

    @abstractmethod
    async def on_load(self) -> bool:
        """Called when plugin is loaded. Return True for success."""
        ...

    @abstractmethod
    async def on_unload(self) -> bool:
        """Called when plugin is unloaded."""
        ...

    async def execute(self, action: str, **kwargs) -> Any:
        """
        Execute a plugin action.

        Args:
            action: Action name
            **kwargs: Action parameters

        Returns:
            Action result
        """
        raise NotImplementedError(f"Plugin {self.meta.name} doesn't implement action: {action}")


class PluginManager:
    """
    Plugin lifecycle manager.

    Plugins are Python modules with a `plugin` class variable
    that is a subclass of BasePlugin.
    """

    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}
        self._meta: Dict[str, PluginMeta] = {}
        self._ensure_dirs()

    def _ensure_dirs(self):
        PLUGIN_DIR.mkdir(parents=True, exist_ok=True)

    def register(self, name: str, plugin_class: Type[BasePlugin]) -> PluginMeta:
        """
        Register a plugin class.

        Args:
            name: Plugin name
            plugin_class: Plugin class (subclass of BasePlugin)

        Returns:
            Plugin metadata
        """
        plugin = plugin_class()
        meta = plugin.meta
        meta.name = name
        meta.status = PluginStatus.LOADED
        meta.loaded_at = datetime.now(timezone.utc).isoformat()

        self._plugins[name] = plugin
        self._meta[name] = meta
        return meta

    async def load(self, name: str) -> bool:
        """Load and initialize a plugin."""
        if name not in self._plugins:
            return False

        plugin = self._plugins[name]
        try:
            success = await plugin.on_load()
            if success:
                self._meta[name].status = PluginStatus.ENABLED
            else:
                self._meta[name].status = PluginStatus.ERROR
                self._meta[name].error = "on_load() returned False"
            return success
        except Exception as e:
            self._meta[name].status = PluginStatus.ERROR
            self._meta[name].error = str(e)
            return False

    async def unload(self, name: str) -> bool:
        """Unload a plugin."""
        if name not in self._plugins:
            return False
        try:
            await self._plugins[name].on_unload()
            self._meta[name].status = PluginStatus.UNLOADED
            return True
        except Exception as e:
            self._meta[name].status = PluginStatus.ERROR
            self._meta[name].error = str(e)
            return False

    async def execute(self, plugin_name: str, action: str, **kwargs) -> Any:
        """Execute a plugin action."""
        if plugin_name not in self._plugins:
            raise KeyError(f"Plugin not found: {plugin_name}")
        if self._meta[plugin_name].status != PluginStatus.ENABLED:
            raise RuntimeError(f"Plugin {plugin_name} is not enabled (status: {self._meta[plugin_name].status})")
        return await self._plugins[plugin_name].execute(action, **kwargs)

    def get(self, name: str) -> Optional[BasePlugin]:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def discover(self) -> List[str]:
        """
        Scan plugin directory for plugins.

        Looks for Python files with a `plugin` class variable.

        Returns:
            List of discovered plugin names
        """
        # TODO: Implement plugin discovery
        # TODO: Scan PLUGIN_DIR for *.py files
        # TODO: Import each, check for plugin class
        # TODO: Auto-register discovered plugins
        return []

    def list_plugins(self) -> List[PluginMeta]:
        """List all registered plugins."""
        return list(self._meta.values())

    def summary(self) -> str:
        """Human-readable plugin summary."""
        plugins = self.list_plugins()
        if not plugins:
            return "No plugins registered."
        lines = [f"🔌 {len(plugins)} plugins:"]
        for p in plugins:
            status_emoji = {"enabled": "✅", "loaded": "📦", "error": "❌", "disabled": "⏸️", "unloaded": "💤"}
            emoji = status_emoji.get(p.status.value if isinstance(p.status, PluginStatus) else p.status, "?")
            lines.append(f"  {emoji} {p.name} v{p.version} — {p.description}")
        return "\n".join(lines)
