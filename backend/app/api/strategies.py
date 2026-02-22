"""Strategies API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.plugins.manager import PluginManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strategies", tags=["Strategies"])


class StrategyConfig(BaseModel):
    """Strategy configuration model."""
    enabled: bool = True
    parameters: dict = {}


def get_plugin_manager() -> PluginManager:
    """Get plugin manager instance."""
    # TODO: Get from app state
    return PluginManager()


@router.get("")
async def get_strategies(plugin_manager: PluginManager = Depends(get_plugin_manager)):
    """
    Get all available strategies.
    
    Returns list of strategy plugins with their status and parameters.
    """
    strategies = []
    
    for name, strategy in plugin_manager.strategy_plugins.items():
        strategies.append({
            "name": name,
            "version": strategy.version,
            "description": strategy.description,
            "initialized": strategy.is_initialized,
            "active": strategy.is_active if hasattr(strategy, 'is_active') else False,
            "parameters": strategy.get_parameters() if hasattr(strategy, 'get_parameters') else {},
        })
    
    return {
        "strategies": strategies,
        "total": len(strategies),
    }


@router.get("/{name}")
async def get_strategy(
    name: str,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
):
    """
    Get a specific strategy by name.
    
    - **name**: Strategy name (e.g., rsi, macd)
    """
    if not plugin_manager.has_strategy(name):
        raise HTTPException(status_code=404, detail=f"Strategy '{name}' not found")
    
    strategy = plugin_manager.get_strategy(name)
    
    return {
        "name": name,
        "version": strategy.version,
        "description": strategy.description,
        "initialized": strategy.is_initialized,
        "active": strategy.is_active if hasattr(strategy, 'is_active') else False,
        "parameters": strategy.get_parameters() if hasattr(strategy, 'get_parameters') else {},
        "symbols": strategy.get_symbols() if hasattr(strategy, 'get_symbols') else [],
        "timeframe": strategy.get_timeframe() if hasattr(strategy, 'get_timeframe') else "1h",
    }


@router.post("/{name}/activate")
async def activate_strategy(
    name: str,
    config: StrategyConfig = None,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
):
    """
    Activate a strategy.
    
    - **name**: Strategy name
    - **config**: Optional configuration
    """
    if not plugin_manager.has_strategy(name):
        raise HTTPException(status_code=404, detail=f"Strategy '{name}' not found")
    
    strategy = plugin_manager.get_strategy(name)
    
    # Set parameters if provided
    if config and config.parameters and hasattr(strategy, 'set_parameters'):
        strategy.set_parameters(config.parameters)
    
    # Activate strategy
    if hasattr(strategy, 'activate'):
        strategy.activate()
    
    logger.info(f"Activated strategy: {name}")
    
    return {
        "status": "success",
        "message": f"Strategy '{name}' activated",
        "name": name,
    }


@router.post("/{name}/deactivate")
async def deactivate_strategy(
    name: str,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
):
    """
    Deactivate a strategy.
    
    - **name**: Strategy name
    """
    if not plugin_manager.has_strategy(name):
        raise HTTPException(status_code=404, detail=f"Strategy '{name}' not found")
    
    strategy = plugin_manager.get_strategy(name)
    
    # Deactivate strategy
    if hasattr(strategy, 'deactivate'):
        strategy.deactivate()
    
    logger.info(f"Deactivated strategy: {name}")
    
    return {
        "status": "success",
        "message": f"Strategy '{name}' deactivated",
        "name": name,
    }


@router.put("/{name}/parameters")
async def update_strategy_parameters(
    name: str,
    parameters: dict,
    plugin_manager: PluginManager = Depends(get_plugin_manager),
):
    """
    Update strategy parameters.
    
    - **name**: Strategy name
    - **parameters**: New parameters
    """
    if not plugin_manager.has_strategy(name):
        raise HTTPException(status_code=404, detail=f"Strategy '{name}' not found")
    
    strategy = plugin_manager.get_strategy(name)
    
    if not hasattr(strategy, 'set_parameters'):
        raise HTTPException(status_code=400, detail="Strategy does not support parameter updates")
    
    strategy.set_parameters(parameters)
    
    logger.info(f"Updated parameters for strategy '{name}': {parameters}")
    
    return {
        "status": "success",
        "message": f"Parameters updated for strategy '{name}'",
        "name": name,
        "parameters": strategy.get_parameters(),
    }
