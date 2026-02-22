"""Server management API routes - restart and update."""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/server", tags=["Server Management"])

# Global state
_server_state = {
    "restart_requested": False,
    "update_requested": False,
    "last_restart": None,
    "last_update": None,
    "update_in_progress": False,
}


class ServerStatus(BaseModel):
    """Server status response."""
    status: str
    uptime_seconds: float | None
    last_restart: str | None
    last_update: str | None
    restart_pending: bool
    update_pending: bool
    version: str


class ActionResponse(BaseModel):
    """Action response."""
    success: bool
    message: str
    timestamp: str


@router.get("/status", response_model=ServerStatus)
async def get_server_status():
    """
    Get detailed server status.
    
    Returns server uptime, restart/update history, and pending actions.
    """
    from app.main import app_state, _startup_time
    
    uptime_seconds = 0
    if _startup_time:
        uptime_seconds = (datetime.utcnow() - _startup_time).total_seconds()
    
    return ServerStatus(
        status="running",
        uptime_seconds=uptime_seconds,
        last_restart=_server_state["last_restart"],
        last_update=_server_state["last_update"],
        restart_pending=app_state.restart_pending or _server_state["restart_requested"],
        update_pending=app_state.update_pending or _server_state["update_requested"],
        version="1.0.0",
    )


@router.post("/restart", response_model=ActionResponse)
async def restart_server():
    """
    Request server restart.
    
    The restart will be performed by the run_server.py supervisor.
    """
    try:
        logger.info("Server restart requested via API")
        
        # Set restart flag
        _server_state["restart_requested"] = True
        _server_state["last_restart"] = datetime.utcnow().isoformat()
        
        from app.main import request_restart
        request_restart()
        
        # Schedule restart using signal
        async def delayed_restart():
            await asyncio.sleep(1)  # Wait for response to be sent
            logger.info("Initiating server restart via signal...")
            os.kill(os.getpid(), signal.SIGTERM)
        
        asyncio.create_task(delayed_restart())
        
        return ActionResponse(
            success=True,
            message="Server restart initiated",
            timestamp=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        logger.error(f"Failed to restart server: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update", response_model=ActionResponse)
async def update_server():
    """
    Request server update from Git.
    
    This will:
    1. Fetch latest changes from GitHub
    2. Pull updates
    3. Restart the server
    """
    try:
        logger.info("Server update requested via API")
        
        if _server_state["update_in_progress"]:
            return ActionResponse(
                success=False,
                message="Update already in progress",
                timestamp=datetime.utcnow().isoformat(),
            )
        
        _server_state["update_in_progress"] = True
        _server_state["update_requested"] = True
        
        # Run update in background
        async def run_update():
            try:
                project_root = Path(__file__).parent.parent.parent.parent
                
                # Fetch latest
                proc = await asyncio.create_subprocess_exec(
                    "git", "fetch", "origin", "gh-pages",
                    cwd=str(project_root),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
                
                # Pull updates
                proc = await asyncio.create_subprocess_exec(
                    "git", "pull", "origin", "gh-pages",
                    cwd=str(project_root),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                
                if proc.returncode == 0:
                    logger.info("Update pulled successfully")
                    _server_state["last_update"] = datetime.utcnow().isoformat()
                    
                    # Restart server
                    await asyncio.sleep(2)
                    logger.info("Initiating restart after update...")
                    os._exit(3)
                else:
                    logger.warning(f"Update failed: {stderr.decode()}")
                    _server_state["update_in_progress"] = False
                    
            except Exception as e:
                logger.error(f"Update error: {e}")
                _server_state["update_in_progress"] = False
        
        asyncio.create_task(run_update())
        
        return ActionResponse(
            success=True,
            message="Server update initiated. Server will restart after update.",
            timestamp=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        logger.error(f"Failed to update server: {e}")
        _server_state["update_in_progress"] = False
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs", response_model=dict)
async def get_server_logs(lines: int = 50):
    """
    Get recent server logs.
    
    Args:
        lines: Number of log lines to return (default: 50)
    """
    from pathlib import Path
    
    log_file = Path(__file__).parent.parent.parent.parent / "logs" / "server.log"
    
    if not log_file.exists():
        return {"logs": [], "count": 0}
    
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        return {
            "logs": [line.strip() for line in recent_lines],
            "count": len(recent_lines),
            "total": len(all_lines),
        }
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        return {"logs": [], "count": 0, "error": str(e)}
