#!/usr/bin/env python3
"""
Crypto Trader - Self-Healing Server with Auto-Update

This script runs the application with:
- Automatic service monitoring and recovery
- Git auto-update functionality
- Real-time terminal logging
- Graceful shutdown handling

Usage:
    python run_server.py [--debug] [--no-auto-update]
"""

import asyncio
import logging
import os
import signal
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.supervisor import Supervisor, ServiceStatus
from app.updater import AutoUpdater
from app.health_monitor import HealthMonitor, HealthCheck, check_api_health
from app.config import settings


# Configure logging
def setup_logging(debug: bool = False):
    """Setup terminal logging."""
    log_level = logging.DEBUG if debug else logging.INFO
    
    # Create custom formatter for terminal
    class TerminalFormatter(logging.Formatter):
        def format(self, record):
            # Add timestamp
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            
            # Color levels
            colors = {
                logging.DEBUG: "\033[36m",     # Cyan
                logging.INFO: "\033[32m",      # Green
                logging.WARNING: "\033[33m",   # Yellow
                logging.ERROR: "\033[31m",     # Red
                logging.CRITICAL: "\033[35m",  # Magenta
            }
            reset = "\033[0m"
            color = colors.get(record.levelno, "")
            
            # Format with component name
            component = record.name.split(".")[-1] if "." in record.name else record.name
            
            return (
                f"{timestamp} | {color}{record.levelname:<8}{reset} | "
                f"{component:<15} | {record.getMessage()}"
            )
    
    # Setup handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(TerminalFormatter())
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


class Server:
    """Main server application."""
    
    def __init__(self, debug: bool = False, auto_update: bool = True):
        self.debug = debug
        self.auto_update_enabled = auto_update
        self.project_root = Path(__file__).parent
        
        self.supervisor: Supervisor | None = None
        self.updater: AutoUpdater | None = None
        self.health_monitor: HealthMonitor | None = None
        
        self._shutdown = False
        self._restart_pending = False
    
    async def initialize(self):
        """Initialize all components."""
        logger = logging.getLogger(__name__)
        logger.info("=" * 60)
        logger.info("🚀 Crypto Trader Server")
        logger.info("=" * 60)
        logger.info(f"Project Root: {self.project_root}")
        logger.info(f"Debug Mode: {self.debug}")
        logger.info(f"Auto-Update: {self.auto_update_enabled}")
        logger.info("=" * 60)
        
        # Initialize Supervisor
        self.supervisor = Supervisor(self.project_root)
        
        # Register API service
        self.supervisor.register_service(
            name="api",
            start_command=[
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--host", settings.HOST,
                "--port", str(settings.PORT),
                "--log-level", "debug" if self.debug else "info",
            ],
            health_check=self._check_api_health,
            restart_delay=5,
            max_restarts=10,
        )
        
        # Initialize Health Monitor
        self.health_monitor = HealthMonitor()
        
        # Add health checks
        self.health_monitor.add_check(HealthCheck(
            name="api",
            check_func=self._check_api_health,
            interval=30,
            max_failures=3,
            on_failure=self._on_api_failure,
            on_recovery=self._on_api_recovery,
        ))
        
        # Initialize Auto-Updater
        if self.auto_update_enabled:
            self.updater = AutoUpdater(
                project_root=self.project_root,
                check_interval=300,  # 5 minutes
                branch="gh-pages",
                on_update=self._on_update,
            )
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        logger.info("Initialization complete")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        loop = asyncio.get_event_loop()
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(self.shutdown()),
            )
    
    async def _check_api_health(self) -> bool:
        """Check API health."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://{settings.HOST}:{settings.PORT}/api/health",
                    timeout=5,
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False
    
    async def _on_api_failure(self):
        """Handle API failure."""
        logger = logging.getLogger(__name__)
        logger.error("API health check failed - triggering restart")
        
        if self.supervisor:
            await self.supervisor.restart_service("api")
    
    async def _on_api_recovery(self):
        """Handle API recovery."""
        logger = logging.getLogger(__name__)
        logger.info("API recovered successfully")
    
    async def _on_update(self):
        """Handle application update."""
        logger = logging.getLogger(__name__)
        logger.info("Update triggered - restarting application...")
        
        self._restart_pending = True
        
        if self.supervisor:
            # Stop all services
            await self.supervisor.stop()
        
        if self.health_monitor:
            await self.health_monitor.stop()
        
        # Restart application
        await self.restart()
    
    async def start(self):
        """Start the server."""
        logger = logging.getLogger(__name__)
        
        try:
            # Start components
            await self.health_monitor.start()
            logger.info("Health Monitor started")
            
            await self.supervisor.start()
            logger.info("Supervisor started")
            
            if self.auto_update_enabled and self.updater:
                await self.updater.start()
                logger.info("Auto-Updater started")
            
            # Main loop
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def _main_loop(self):
        """Main server loop - displays status."""
        logger = logging.getLogger(__name__)
        status_interval = 60  # Show status every 60 seconds
        last_status = datetime.utcnow()
        
        while not self._shutdown:
            try:
                # Show status periodically
                now = datetime.utcnow()
                if (now - last_status).total_seconds() >= status_interval:
                    self._print_status()
                    last_status = now
                
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                break
    
    def _print_status(self):
        """Print current status to terminal."""
        logger = logging.getLogger(__name__)
        
        status_lines = [
            "",
            "=" * 60,
            "📊 SERVER STATUS",
            "=" * 60,
        ]
        
        # Supervisor status
        if self.supervisor:
            status = self.supervisor.get_status()
            status_lines.append(f"Supervisor: {'✅ Running' if status['running'] else '❌ Stopped'}")
            
            for name, svc in status["services"].items():
                icon = "✅" if svc["status"] == "running" else "❌"
                status_lines.append(f"  {icon} {name}: {svc['status']} (restarts: {svc['restart_count']})")
        
        # Health status
        if self.health_monitor:
            health = self.health_monitor.get_status()
            status_lines.append(
                f"Health: {'✅ All healthy' if health['healthy'] else '⚠️ Issues detected'}"
            )
        
        # Updater status
        if self.updater and self.auto_update_enabled:
            update_status = self.updater.get_status()
            commit = update_status["current_commit"][:8] if update_status["current_commit"] else "unknown"
            status_lines.append(f"Auto-Update: ✅ Enabled (commit: {commit})")
        
        status_lines.append("=" * 60)
        
        for line in status_lines:
            logger.info(line)
    
    async def restart(self):
        """Restart the application."""
        logger = logging.getLogger(__name__)
        logger.info("Restarting application...")

        # Re-exec the current script
        os.execv(sys.executable, [sys.executable, __file__] + sys.argv[1:])

    async def run(self):
        """Run the server with restart support."""
        while True:
            try:
                await self.initialize()
                await self.start()
                
                # Wait for shutdown or restart signal
                await self.wait_for_shutdown()
                
                # Check if restart was requested
                if self._restart_pending:
                    logger.info("Restart requested, restarting...")
                    self._restart_pending = False
                    await self.cleanup()
                    continue
                else:
                    break
                    
            except Exception as e:
                logger.error(f"Server error: {e}")
                if self.debug:
                    import traceback
                    traceback.print_exc()
                
                # Auto-restart on crash
                logger.info("Auto-restarting in 5 seconds...")
                await asyncio.sleep(5)
                await self.cleanup()
                continue
        
        await self.cleanup()

    async def wait_for_shutdown(self):
        """Wait for shutdown or restart signal."""
        await self.shutdown_event.wait()
    
    async def shutdown(self):
        """Graceful shutdown."""
        if self._shutdown:
            return
        
        logger = logging.getLogger(__name__)
        logger.info("Shutdown requested...")
        
        self._shutdown = True
        
        if self.supervisor:
            self.supervisor.request_shutdown()
    
    async def cleanup(self):
        """Cleanup resources."""
        logger = logging.getLogger(__name__)
        logger.info("Cleaning up...")
        
        if self.updater:
            await self.updater.stop()
        
        if self.health_monitor:
            await self.health_monitor.stop()
        
        if self.supervisor:
            await self.supervisor.stop()
        
        logger.info("Cleanup complete")
        logger.info("=" * 60)
        logger.info("👋 Server stopped")
        logger.info("=" * 60)


async def main():
    """Main entry point."""
    # Parse arguments
    debug = "--debug" in sys.argv
    no_auto_update = "--no-auto-update" in sys.argv

    # Setup logging
    logger = setup_logging(debug)

    # Create and run server
    server = Server(debug=debug, auto_update=not no_auto_update)

    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Server crashed: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
