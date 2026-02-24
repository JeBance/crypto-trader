"""Plugin Manager for loading and managing plugins."""

import importlib
import logging
from pathlib import Path
from typing import TypeVar

from app.core.exceptions import PluginLoadError, PluginNotFoundError
from app.plugins.base import Plugin, ExchangePlugin, StrategyPlugin, NotifierPlugin

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Plugin)


class PluginManager:
    """
    Plugin Manager for discovering, loading, and managing plugins.
    
    Supports auto-discovery of plugins from specified directories
    and provides methods for accessing plugins by type and name.
    """
    
    def __init__(self):
        self._plugins: dict[str, Plugin] = {}
        self._exchange_plugins: dict[str, ExchangePlugin] = {}
        self._strategy_plugins: dict[str, StrategyPlugin] = {}
        self._notifier_plugins: dict[str, NotifierPlugin] = {}
    
    @property
    def all_plugins(self) -> dict[str, Plugin]:
        """Get all registered plugins."""
        return self._plugins.copy()
    
    @property
    def exchange_plugins(self) -> dict[str, ExchangePlugin]:
        """Get all exchange plugins."""
        return self._exchange_plugins.copy()
    
    @property
    def strategy_plugins(self) -> dict[str, StrategyPlugin]:
        """Get all strategy plugins."""
        return self._strategy_plugins.copy()
    
    @property
    def notifier_plugins(self) -> dict[str, NotifierPlugin]:
        """Get all notifier plugins."""
        return self._notifier_plugins.copy()
    
    def register(self, plugin: Plugin) -> None:
        """
        Register a plugin.
        
        Args:
            plugin: Plugin instance to register
        """
        self._plugins[plugin.name] = plugin
        
        if isinstance(plugin, ExchangePlugin):
            self._exchange_plugins[plugin.name] = plugin
            logger.info(f"Registered exchange plugin: {plugin.name} v{plugin.version}")
        elif isinstance(plugin, StrategyPlugin):
            self._strategy_plugins[plugin.name] = plugin
            logger.info(f"Registered strategy plugin: {plugin.name} v{plugin.version}")
        elif isinstance(plugin, NotifierPlugin):
            self._notifier_plugins[plugin.name] = plugin
            logger.info(f"Registered notifier plugin: {plugin.name} v{plugin.version}")
        else:
            logger.info(f"Registered plugin: {plugin.name} v{plugin.version}")
    
    def unregister(self, name: str) -> None:
        """
        Unregister a plugin by name.
        
        Args:
            name: Plugin name
        """
        if name not in self._plugins:
            raise PluginNotFoundError(f"Plugin '{name}' not found")
        
        plugin = self._plugins.pop(name)
        
        if isinstance(plugin, ExchangePlugin):
            self._exchange_plugins.pop(name, None)
        elif isinstance(plugin, StrategyPlugin):
            self._strategy_plugins.pop(name, None)
        elif isinstance(plugin, NotifierPlugin):
            self._notifier_plugins.pop(name, None)
        
        logger.info(f"Unregistered plugin: {name}")
    
    def get_plugin(self, name: str) -> Plugin:
        """
        Get a plugin by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin instance
            
        Raises:
            PluginNotFoundError: If plugin not found
        """
        if name not in self._plugins:
            raise PluginNotFoundError(f"Plugin '{name}' not found")
        return self._plugins[name]
    
    def get_exchange(self, name: str) -> ExchangePlugin:
        """
        Get an exchange plugin by name.
        
        Args:
            name: Exchange name
            
        Returns:
            Exchange plugin instance
            
        Raises:
            PluginNotFoundError: If exchange not found
        """
        if name not in self._exchange_plugins:
            raise PluginNotFoundError(f"Exchange '{name}' not found")
        return self._exchange_plugins[name]
    
    def get_strategy(self, name: str) -> StrategyPlugin:
        """
        Get a strategy plugin by name.
        
        Args:
            name: Strategy name
            
        Returns:
            Strategy plugin instance
            
        Raises:
            PluginNotFoundError: If strategy not found
        """
        if name not in self._strategy_plugins:
            raise PluginNotFoundError(f"Strategy '{name}' not found")
        return self._strategy_plugins[name]
    
    def get_notifier(self, name: str) -> NotifierPlugin:
        """
        Get a notifier plugin by name.
        
        Args:
            name: Notifier name
            
        Returns:
            Notifier plugin instance
            
        Raises:
            PluginNotFoundError: If notifier not found
        """
        if name not in self._notifier_plugins:
            raise PluginNotFoundError(f"Notifier '{name}' not found")
        return self._notifier_plugins[name]
    
    def has_plugin(self, name: str) -> bool:
        """Check if a plugin is registered."""
        return name in self._plugins
    
    def has_exchange(self, name: str) -> bool:
        """Check if an exchange plugin is registered."""
        return name in self._exchange_plugins
    
    def has_strategy(self, name: str) -> bool:
        """Check if a strategy plugin is registered."""
        return name in self._strategy_plugins
    
    def has_notifier(self, name: str) -> bool:
        """Check if a notifier plugin is registered."""
        return name in self._notifier_plugins
    
    async def initialize_all(self) -> None:
        """Initialize all registered plugins."""
        logger.info(f"Initializing {len(self._plugins)} plugins...")
        
        for name, plugin in self._plugins.items():
            try:
                await plugin.initialize()
                logger.info(f"Plugin '{name}' initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize plugin '{name}': {e}")
                raise
    
    async def shutdown_all(self) -> None:
        """Shutdown all registered plugins."""
        logger.info(f"Shutting down {len(self._plugins)} plugins...")
        
        for name, plugin in list(self._plugins.items()):
            try:
                await plugin.shutdown()
                logger.info(f"Plugin '{name}' shutdown successfully")
            except Exception as e:
                logger.error(f"Error shutting down plugin '{name}': {e}")
    
    def discover(self, plugin_dir: Path, plugin_type: type[T] | None = None) -> list[str]:
        """
        Discover and load plugins from a directory.
        
        Args:
            plugin_dir: Directory to search for plugins
            plugin_type: Optional filter by plugin type
            
        Returns:
            List of discovered plugin names
        """
        discovered = []
        
        if not plugin_dir.exists():
            logger.warning(f"Plugin directory does not exist: {plugin_dir}")
            return discovered
        
        logger.info(f"Discovering plugins in: {plugin_dir}")
        
        for file in plugin_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue
            
            module_name = f"{plugin_dir.name}.{file.stem}"
            
            # Convert path to module path
            if plugin_dir.parts[0] == "app":
                module_name = ".".join(plugin_dir.parts) + "." + file.stem
            else:
                module_name = f"app.{plugin_dir.name}.{file.stem}"
            
            try:
                module = importlib.import_module(module_name)
                
                # Find plugin classes in module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    
                    # Skip non-classes and base classes
                    if not isinstance(attr, type):
                        continue
                    if attr_name.startswith("_"):
                        continue
                    if attr == Plugin or attr == ExchangePlugin or attr == StrategyPlugin or attr == NotifierPlugin:
                        continue
                    
                    # Check if it's a plugin subclass
                    if plugin_type:
                        if issubclass(attr, plugin_type) and attr != plugin_type:
                            plugin = attr()
                            self.register(plugin)
                            discovered.append(plugin.name)
                    else:
                        if issubclass(attr, Plugin) and attr != Plugin:
                            plugin = attr()
                            self.register(plugin)
                            discovered.append(plugin.name)
                            
            except Exception as e:
                logger.error(f"Error loading plugin from {module_name}: {e}")
        
        logger.info(f"Discovered {len(discovered)} plugins")
        return discovered
    
    def load_module(self, module_path: str, class_name: str, **kwargs) -> Plugin:
        """
        Load a plugin from a specific module and class.
        
        Args:
            module_path: Python module path (e.g., "app.exchanges.binance")
            class_name: Plugin class name
            **kwargs: Arguments to pass to plugin constructor
            
        Returns:
            Plugin instance
            
        Raises:
            PluginLoadError: If plugin cannot be loaded
        """
        try:
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, class_name)
            
            if not issubclass(plugin_class, Plugin):
                raise PluginLoadError(f"Class '{class_name}' is not a Plugin subclass")
            
            plugin = plugin_class(**kwargs)
            self.register(plugin)
            
            logger.info(f"Loaded plugin: {class_name} from {module_path}")
            return plugin
            
        except ImportError as e:
            raise PluginLoadError(f"Failed to import module '{module_path}': {e}")
        except AttributeError as e:
            raise PluginLoadError(f"Class '{class_name}' not found in module '{module_path}': {e}")
        except Exception as e:
            raise PluginLoadError(f"Failed to load plugin: {e}")
    
    def get_info(self) -> dict:
        """
        Get information about all registered plugins.
        
        Returns:
            Dictionary with plugin information
        """
        return {
            "total": len(self._plugins),
            "exchanges": {name: p.get_info() for name, p in self._exchange_plugins.items()},
            "strategies": {name: p.get_info() for name, p in self._strategy_plugins.items()},
            "notifiers": {name: p.get_info() for name, p in self._notifier_plugins.items()},
        }
