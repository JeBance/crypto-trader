"""
Crypto Trader - Self-Healing Server Application

This package provides:
- Supervisor: Service monitoring and auto-restart
- AutoUpdater: Git-based auto-update
- HealthMonitor: Component health checking
"""

from app.supervisor import Supervisor, ServiceStatus, ServiceInfo
from app.updater import AutoUpdater
from app.health_monitor import HealthMonitor, HealthCheck

__all__ = [
    "Supervisor",
    "ServiceStatus",
    "ServiceInfo",
    "AutoUpdater",
    "HealthMonitor",
    "HealthCheck",
]
