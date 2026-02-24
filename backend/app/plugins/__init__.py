"""Plugin system for exchanges, strategies, and notifiers."""

from app.plugins.base import Plugin, ExchangePlugin, StrategyPlugin, NotifierPlugin
from app.plugins.manager import PluginManager

__all__ = [
    "Plugin",
    "ExchangePlugin",
    "StrategyPlugin",
    "NotifierPlugin",
    "PluginManager",
]
