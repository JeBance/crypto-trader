"""
Health Monitor for application components

Monitors the health of various application components and triggers recovery.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)


class HealthCheck:
    """
    Health check for a component.
    
    Attributes:
        name: Component name
        check_func: Async function that returns True if healthy
        interval: How often to check (seconds)
        timeout: Timeout for check function (seconds)
        max_failures: Max consecutive failures before triggering action
        on_failure: Callback when component is unhealthy
        on_recovery: Callback when component recovers
    """
    
    def __init__(
        self,
        name: str,
        check_func: Callable[[], Any],
        interval: int = 30,
        timeout: int = 10,
        max_failures: int = 3,
        on_failure: Optional[Callable[[], Any]] = None,
        on_recovery: Optional[Callable[[], Any]] = None,
    ):
        self.name = name
        self.check_func = check_func
        self.interval = interval
        self.timeout = timeout
        self.max_failures = max_failures
        self.on_failure = on_failure
        self.on_recovery = on_recovery
        
        self.consecutive_failures = 0
        self.is_healthy = True
        self.last_check: datetime | None = None
        self.last_failure: datetime | None = None
        self._running = False
        self._task: asyncio.Task | None = None
    
    async def start(self) -> None:
        """Start health monitoring."""
        logger.info(f"Starting health monitor for: {self.name}")
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
    
    async def stop(self) -> None:
        """Stop health monitoring."""
        logger.info(f"Stopping health monitor for: {self.name}")
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                await self._check()
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error for {self.name}: {e}")
                await asyncio.sleep(5)
    
    async def _check(self) -> None:
        """Perform health check."""
        try:
            result = await asyncio.wait_for(
                self.check_func(),
                timeout=self.timeout,
            )
            
            self.last_check = datetime.utcnow()
            
            if result:
                # Component is healthy
                if not self.is_healthy:
                    logger.info(f"Component '{self.name}' recovered!")
                    self.is_healthy = True
                    self.consecutive_failures = 0
                    
                    if self.on_recovery:
                        await self._call_callback(self.on_recovery)
            else:
                # Component is unhealthy
                await self._handle_failure()
                
        except asyncio.TimeoutError:
            logger.warning(f"Health check timeout for: {self.name}")
            await self._handle_failure()
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            await self._handle_failure()
    
    async def _handle_failure(self) -> None:
        """Handle health check failure."""
        self.consecutive_failures += 1
        self.last_failure = datetime.utcnow()
        
        logger.warning(
            f"Component '{self.name}' unhealthy "
            f"({self.consecutive_failures}/{self.max_failures})"
        )
        
        if self.consecutive_failures >= self.max_failures:
            if self.is_healthy:
                self.is_healthy = False
                logger.error(f"Component '{self.name}' marked as FAILED")
                
                if self.on_failure:
                    await self._call_callback(self.on_failure)
    
    async def _call_callback(self, callback: Callable[[], Any]) -> None:
        """Call a callback safely."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback()
            else:
                callback()
        except Exception as e:
            logger.error(f"Callback error for {self.name}: {e}")
    
    def get_status(self) -> dict:
        """Get health check status."""
        return {
            "name": self.name,
            "healthy": self.is_healthy,
            "consecutive_failures": self.consecutive_failures,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
        }


class HealthMonitor:
    """
    Central health monitor for all components.
    
    Manages multiple health checks and provides aggregate status.
    """
    
    def __init__(self):
        self.checks: dict[str, HealthCheck] = {}
        self._running = False
    
    def add_check(self, check: HealthCheck) -> None:
        """
        Add a health check.
        
        Args:
            check: HealthCheck instance
        """
        self.checks[check.name] = check
        logger.info(f"Added health check: {check.name}")
    
    def remove_check(self, name: str) -> None:
        """
        Remove a health check.
        
        Args:
            name: Check name
        """
        if name in self.checks:
            self.checks.pop(name)
            logger.info(f"Removed health check: {name}")
    
    async def start(self) -> None:
        """Start all health monitors."""
        logger.info(f"Starting Health Monitor ({len(self.checks)} checks)")
        self._running = True
        
        for check in self.checks.values():
            await check.start()
        
        logger.info("Health Monitor started")
    
    async def stop(self) -> None:
        """Stop all health monitors."""
        logger.info("Stopping Health Monitor")
        self._running = False
        
        for check in self.checks.values():
            await check.stop()
        
        logger.info("Health Monitor stopped")
    
    def is_healthy(self) -> bool:
        """Check if all components are healthy."""
        return all(check.is_healthy for check in self.checks.values())
    
    def get_status(self) -> dict:
        """Get health monitor status."""
        return {
            "running": self._running,
            "healthy": self.is_healthy(),
            "checks": {
                name: check.get_status()
                for name, check in self.checks.items()
            },
            "summary": {
                "total": len(self.checks),
                "healthy": sum(1 for c in self.checks.values() if c.is_healthy),
                "unhealthy": sum(1 for c in self.checks.values() if not c.is_healthy),
            },
        }


# Pre-built health checks for common components

async def check_api_health(base_url: str = "http://localhost:8000") -> bool:
    """Check if API is responding."""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/api/health", timeout=5) as resp:
                return resp.status == 200
    except Exception:
        return False


async def check_database_health(db_url: str) -> bool:
    """Check if database is accessible."""
    try:
        # Simple file existence check for SQLite
        from pathlib import Path
        db_path = Path(db_url.replace("sqlite+aiosqlite:///", ""))
        return db_path.exists()
    except Exception:
        return False


async def check_process_health(pid: int) -> bool:
    """Check if a process is running."""
    try:
        import os
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False
    except Exception:
        return False
