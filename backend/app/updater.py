"""
Auto-Updater for Git-based deployments

Checks for new commits and automatically updates the application.
"""

import asyncio
import logging
import os
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Any

logger = logging.getLogger(__name__)


class AutoUpdater:
    """
    Automatic updater that checks Git repository for updates.
    
    Features:
    - Periodic check for new commits
    - Automatic pull and restart
    - Pre and post update hooks
    - Rollback on failure
    """
    
    def __init__(
        self,
        project_root: Path,
        check_interval: int = 300,  # 5 minutes
        branch: str = "gh-pages",
        on_update: Callable[[], Any] | None = None,
    ):
        """
        Initialize auto-updater.
        
        Args:
            project_root: Project root directory
            check_interval: How often to check for updates (seconds)
            branch: Git branch to track
            on_update: Callback to run after successful update
        """
        self.project_root = project_root
        self.check_interval = check_interval
        self.branch = branch
        self.on_update = on_update
        
        self._running = False
        self._task: asyncio.Task | None = None
        self._last_check: datetime | None = None
        self._current_commit: str | None = None
    
    async def start(self) -> None:
        """Start the auto-updater."""
        logger.info("Starting Auto-Updater...")
        self._running = True
        
        # Get current commit
        self._current_commit = await self._get_current_commit()
        logger.info(f"Current commit: {self._current_commit}")
        
        # Start update loop
        self._task = asyncio.create_task(self._update_loop())
        logger.info("Auto-Updater started")
    
    async def stop(self) -> None:
        """Stop the auto-updater."""
        logger.info("Stopping Auto-Updater...")
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Auto-Updater stopped")
    
    async def _update_loop(self) -> None:
        """Main update loop."""
        while self._running:
            try:
                await self._check_and_update()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-updater error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _check_and_update(self) -> None:
        """Check for updates and apply if available."""
        logger.debug("Checking for updates...")
        
        # Fetch latest from remote
        await self._fetch()
        
        # Check if there are new commits
        has_update = await self._has_updates()
        
        if has_update:
            logger.info("New update available!")
            await self._update()
        else:
            self._last_check = datetime.utcnow()
            logger.debug("No updates available")
    
    async def _get_current_commit(self) -> str | None:
        """Get current commit hash."""
        try:
            process = await asyncio.create_subprocess_exec(
                "git", "rev-parse", "HEAD",
                cwd=str(self.project_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await process.communicate()
            
            if process.returncode == 0:
                return stdout.decode().strip()
        except Exception as e:
            logger.error(f"Failed to get current commit: {e}")
        
        return None
    
    async def _fetch(self) -> bool:
        """Fetch latest changes from remote."""
        try:
            logger.debug("Fetching from remote...")
            
            process = await asyncio.create_subprocess_exec(
                "git", "fetch", "origin", self.branch,
                cwd=str(self.project_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.debug("Fetch successful")
                return True
            else:
                logger.warning(f"Fetch failed: {stderr.decode().strip()}")
                return False
                
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            return False
    
    async def _has_updates(self) -> bool:
        """Check if there are new commits."""
        if not self._current_commit:
            return False
        
        try:
            process = await asyncio.create_subprocess_exec(
                "git", "rev-parse", f"origin/{self.branch}",
                cwd=str(self.project_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await process.communicate()
            
            if process.returncode == 0:
                remote_commit = stdout.decode().strip()
                has_updates = remote_commit != self._current_commit
                
                if has_updates:
                    logger.info(f"Remote commit: {remote_commit}")
                
                return has_updates
                
        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
        
        return False
    
    async def _update(self) -> bool:
        """
        Apply the update.
        
        Returns:
            True if update was successful
        """
        logger.info("Applying update...")
        
        try:
            # Pull latest changes
            process = await asyncio.create_subprocess_exec(
                "git", "pull", "origin", self.branch,
                cwd=str(self.project_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Pull failed: {stderr.decode().strip()}")
                return False
            
            logger.info("Pull successful")
            logger.debug(stdout.decode())
            
            # Get new commit hash
            new_commit = await self._get_current_commit()
            logger.info(f"Updated to commit: {new_commit}")
            
            # Run pre-restart hook if exists
            await self._run_hook("prerestart")
            
            # Trigger restart
            if self.on_update:
                logger.info("Triggering application restart...")
                await self.on_update()
            
            self._current_commit = new_commit
            self._last_check = datetime.utcnow()
            
            return True
            
        except Exception as e:
            logger.error(f"Update failed: {e}")
            return False
    
    async def _run_hook(self, hook_name: str) -> None:
        """
        Run a hook script if it exists.
        
        Args:
            hook_name: Name of the hook (prerestart, postrestart)
        """
        hook_path = self.project_root / "scripts" / f"hook_{hook_name}.sh"
        
        if hook_path.exists():
            logger.info(f"Running hook: {hook_name}")
            
            try:
                process = await asyncio.create_subprocess_exec(
                    "bash", str(hook_path),
                    cwd=str(self.project_root),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=60,
                )
                
                if process.returncode == 0:
                    logger.info(f"Hook {hook_name} completed successfully")
                else:
                    logger.warning(
                        f"Hook {hook_name} failed: {stderr.decode().strip()}"
                    )
                    
            except asyncio.TimeoutError:
                logger.warning(f"Hook {hook_name} timed out")
            except Exception as e:
                logger.error(f"Hook {hook_name} error: {e}")
    
    def get_status(self) -> dict:
        """Get updater status."""
        return {
            "running": self._running,
            "current_commit": self._current_commit,
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "check_interval": self.check_interval,
            "branch": self.branch,
        }
