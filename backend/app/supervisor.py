"""
Server Supervisor with Auto-Recovery and Auto-Update

This module provides:
- Service monitoring and automatic restart
- Git auto-update functionality
- Health checking for all components
- Real-time logging to terminal
"""

import asyncio
import logging
import os
import signal
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Coroutine, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service status enumeration."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    RESTARTING = "restarting"


@dataclass
class ServiceInfo:
    """Service information."""
    name: str
    start_command: list[str]
    status: ServiceStatus = ServiceStatus.STOPPED
    restart_count: int = 0
    last_start: datetime | None = None
    last_stop: datetime | None = None
    pid: int | None = None
    process: asyncio.subprocess.Process | None = None
    health_check: Optional[Callable[[], Coroutine[Any, Any, bool]]] = None
    restart_delay: int = 5  # seconds
    max_restarts: int = 5  # max restarts before giving up
    restart_window: int = 300  # time window for max restarts (seconds)
    restart_times: list[datetime] = field(default_factory=list)


class Supervisor:
    """
    Service supervisor with auto-recovery.
    
    Monitors services and automatically restarts them on failure.
    Implements exponential backoff for restarts.
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.services: dict[str, ServiceInfo] = {}
        self.running = False
        self._monitor_task: asyncio.Task | None = None
        self._update_task: asyncio.Task | None = None
        self.shutdown_event = asyncio.Event()
    
    def register_service(
        self,
        name: str,
        start_command: list[str],
        health_check: Optional[Callable[[], Coroutine[Any, Any, bool]]] = None,
        restart_delay: int = 5,
        max_restarts: int = 5,
    ) -> None:
        """
        Register a service for monitoring.
        
        Args:
            name: Service name
            start_command: Command to start the service
            health_check: Async function to check service health
            restart_delay: Delay between restarts in seconds
            max_restarts: Maximum restarts before giving up
        """
        self.services[name] = ServiceInfo(
            name=name,
            start_command=start_command,
            health_check=health_check,
            restart_delay=restart_delay,
            max_restarts=max_restarts,
        )
        logger.info(f"Registered service: {name}")
    
    async def start_service(self, name: str) -> bool:
        """
        Start a service.
        
        Args:
            name: Service name
            
        Returns:
            True if started successfully
        """
        if name not in self.services:
            logger.error(f"Service '{name}' not found")
            return False
        
        service = self.services[name]
        
        if service.status == ServiceStatus.RUNNING:
            logger.warning(f"Service '{name}' is already running")
            return True
        
        try:
            logger.info(f"Starting service: {name}")
            service.status = ServiceStatus.STARTING
            
            # Start process
            service.process = await asyncio.create_subprocess_exec(
                *service.start_command,
                cwd=str(self.project_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            service.pid = service.process.pid
            service.last_start = datetime.utcnow()
            service.status = ServiceStatus.RUNNING
            
            logger.info(f"Service '{name}' started with PID {service.pid}")
            
            # Start output reader
            asyncio.create_task(self._read_service_output(service))
            
            # Wait for process
            asyncio.create_task(self._wait_for_service(service))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start service '{name}': {e}")
            service.status = ServiceStatus.FAILED
            return False
    
    async def stop_service(self, name: str) -> None:
        """
        Stop a service.
        
        Args:
            name: Service name
        """
        if name not in self.services:
            return
        
        service = self.services[name]
        
        if service.process and service.process.pid:
            logger.info(f"Stopping service: {name} (PID {service.process.pid})")
            
            try:
                service.process.terminate()
                await asyncio.wait_for(service.process.wait(), timeout=10)
            except asyncio.TimeoutError:
                logger.warning(f"Service '{name}' didn't terminate gracefully, killing...")
                service.process.kill()
            except Exception as e:
                logger.error(f"Error stopping service '{name}': {e}")
        
        service.status = ServiceStatus.STOPPED
        service.last_stop = datetime.utcnow()
        logger.info(f"Service '{name}' stopped")
    
    async def restart_service(self, name: str) -> bool:
        """
        Restart a service with rate limiting.
        
        Args:
            name: Service name
            
        Returns:
            True if restarted successfully
        """
        if name not in self.services:
            return False
        
        service = self.services[name]
        now = datetime.utcnow()
        
        # Clean old restart times
        service.restart_times = [
            t for t in service.restart_times
            if (now - t).total_seconds() < service.restart_window
        ]
        
        # Check max restarts
        if len(service.restart_times) >= service.max_restarts:
            logger.error(
                f"Service '{name}' exceeded max restarts "
                f"({service.max_restarts} in {service.restart_window}s). Giving up."
            )
            service.status = ServiceStatus.FAILED
            return False
        
        service.restart_times.append(now)
        service.restart_count += 1
        
        logger.info(
            f"Restarting service '{name}' "
            f"(attempt {service.restart_count}/{service.max_restarts})"
        )
        
        service.status = ServiceStatus.RESTARTING
        
        # Stop if running
        if service.process:
            await self.stop_service(name)
        
        # Wait before restart
        await asyncio.sleep(service.restart_delay)
        
        # Start
        return await self.start_service(name)
    
    async def _wait_for_service(self, service: ServiceInfo) -> None:
        """Wait for service process to exit and handle restart."""
        if not service.process:
            return
        
        try:
            returncode = await service.process.wait()
            logger.warning(
                f"Service '{service.name}' exited with code {returncode}"
            )
            
            if self.running and service.status != ServiceStatus.STOPPED:
                service.status = ServiceStatus.FAILED
                
                # Auto-restart
                asyncio.create_task(self.restart_service(service.name))
                
        except Exception as e:
            logger.error(f"Error waiting for service '{service.name}': {e}")
    
    async def _read_service_output(self, service: ServiceInfo) -> None:
        """Read and log service output."""
        if not service.process:
            return
        
        async def read_stream(stream, prefix: str):
            while stream and not stream.at_eof():
                try:
                    line = await stream.readline()
                    if line:
                        logger.info(f"[{service.name}] {prefix} {line.decode().strip()}")
                except Exception as e:
                    logger.debug(f"Error reading output from {service.name}: {e}")
                    break
        
        await asyncio.gather(
            read_stream(service.process.stdout, "OUT"),
            read_stream(service.process.stderr, "ERR"),
        )
    
    async def health_monitor_loop(self) -> None:
        """Monitor health of all services."""
        while self.running:
            try:
                for service in self.services.values():
                    if service.status != ServiceStatus.RUNNING:
                        continue
                    
                    if service.health_check:
                        try:
                            healthy = await service.health_check()
                            if not healthy:
                                logger.warning(
                                    f"Service '{service.name}' health check failed"
                                )
                                asyncio.create_task(self.restart_service(service.name))
                        except Exception as e:
                            logger.error(
                                f"Health check error for '{service.name}': {e}"
                            )
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(5)
    
    async def start(self) -> None:
        """Start the supervisor and all services."""
        logger.info("Starting Supervisor...")
        self.running = True
        self.shutdown_event.clear()
        
        # Start all services
        for name in self.services:
            await self.start_service(name)
        
        # Start health monitor
        self._monitor_task = asyncio.create_task(self.health_monitor_loop())
        
        logger.info("Supervisor started")
        
        # Wait for shutdown signal
        await self.shutdown_event.wait()
    
    async def stop(self) -> None:
        """Stop the supervisor and all services."""
        logger.info("Stopping Supervisor...")
        self.running = False
        
        # Cancel tasks
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        
        # Stop all services
        for name in list(self.services.keys()):
            await self.stop_service(name)
        
        logger.info("Supervisor stopped")
        self.shutdown_event.set()
    
    def request_shutdown(self) -> None:
        """Request supervisor shutdown."""
        logger.info("Shutdown requested")
        asyncio.create_task(self.stop())
    
    def get_status(self) -> dict:
        """Get supervisor status."""
        return {
            "running": self.running,
            "services": {
                name: {
                    "status": svc.status.value,
                    "pid": svc.pid,
                    "restart_count": svc.restart_count,
                    "last_start": svc.last_start.isoformat() if svc.last_start else None,
                }
                for name, svc in self.services.items()
            },
        }
