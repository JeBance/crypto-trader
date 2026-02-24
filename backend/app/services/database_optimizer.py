"""Database optimization service for SQLite."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """
    Database optimization service for SQLite.
    
    Features:
    - VACUUM (reclaim disk space)
    - ANALYZE (update statistics)
    - Index management
    - Integrity checks
    - Optimization scheduling
    
    Usage:
        >>> optimizer = DatabaseOptimizer(db_session)
        >>> await optimizer.vacuum()
        >>> await optimizer.analyze()
        >>> await optimizer.optimize_all()
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self._last_vacuum: Optional[datetime] = None
        self._last_analyze: Optional[datetime] = None
    
    async def vacuum(self) -> bool:
        """
        Run VACUUM to reclaim disk space.
        
        VACUUM rebuilds the database file, reclaiming unused space.
        This can take a while for large databases.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Starting database VACUUM...")
            start_time = datetime.now(timezone.utc)
            
            # VACUUM cannot run in a transaction
            await self.db_session.commit()
            
            # Execute VACUUM
            await self.db_session.execute(text("VACUUM"))
            
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            self._last_vacuum = datetime.now(timezone.utc)
            
            logger.info(f"Database VACUUM completed in {elapsed:.2f} seconds")
            return True
        
        except Exception as e:
            logger.error(f"Database VACUUM failed: {e}")
            return False
    
    async def analyze(self) -> bool:
        """
        Run ANALYZE to update statistics.
        
        ANALYZE computes statistics about indices for query optimization.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Starting database ANALYZE...")
            start_time = datetime.now(timezone.utc)
            
            await self.db_session.execute(text("ANALYZE"))
            
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            self._last_analyze = datetime.now(timezone.utc)
            
            logger.info(f"Database ANALYZE completed in {elapsed:.2f} seconds")
            return True
        
        except Exception as e:
            logger.error(f"Database ANALYZE failed: {e}")
            return False
    
    async def check_integrity(self) -> bool:
        """
        Run integrity check.
        
        Returns:
            True if database is intact, False otherwise
        """
        try:
            logger.info("Running database integrity check...")
            
            result = await self.db_session.execute(text("PRAGMA integrity_check"))
            row = result.first()
            
            if row and row[0] == "ok":
                logger.info("Database integrity check passed")
                return True
            else:
                logger.error(f"Database integrity check failed: {row}")
                return False
        
        except Exception as e:
            logger.error(f"Database integrity check failed: {e}")
            return False
    
    async def get_database_size(self) -> Optional[int]:
        """
        Get database file size in bytes.
        
        Returns:
            Size in bytes, or None if error
        """
        try:
            result = await self.db_session.execute(text("PRAGMA page_size"))
            page_size = result.scalar()
            
            result = await self.db_session.execute(text("PRAGMA page_count"))
            page_count = result.scalar()
            
            if page_size and page_count:
                return page_size * page_count
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get database size: {e}")
            return None
    
    async def get_table_sizes(self) -> dict:
        """
        Get size information for each table.
        
        Returns:
            Dictionary with table sizes
        """
        try:
            query = """
                SELECT 
                    name as table_name,
                    (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=t.name) as exists_flag
                FROM sqlite_master t
                WHERE type='table'
                ORDER BY name
            """
            
            result = await self.db_session.execute(text(query))
            tables = result.fetchall()
            
            sizes = {}
            for table in tables:
                table_name = table[0]
                if not table_name.startswith('sqlite_'):
                    # Get row count
                    count_result = await self.db_session.execute(
                        text(f"SELECT COUNT(*) FROM {table_name}")
                    )
                    count = count_result.scalar()
                    sizes[table_name] = {"rows": count or 0}
            
            return sizes
        
        except Exception as e:
            logger.error(f"Failed to get table sizes: {e}")
            return {}
    
    async def optimize_all(self) -> dict:
        """
        Run full optimization sequence.
        
        Sequence:
        1. Integrity check
        2. VACUUM
        3. ANALYZE
        
        Returns:
            Dictionary with optimization results
        """
        logger.info("Starting full database optimization...")
        start_time = datetime.now(timezone.utc)
        
        results = {
            "integrity_check": False,
            "vacuum": False,
            "analyze": False,
            "duration_seconds": 0,
        }
        
        # 1. Integrity check
        results["integrity_check"] = await self.check_integrity()
        if not results["integrity_check"]:
            logger.warning("Integrity check failed, skipping optimization")
            return results
        
        # 2. VACUUM
        results["vacuum"] = await self.vacuum()
        
        # 3. ANALYZE
        results["analyze"] = await self.analyze()
        
        results["duration_seconds"] = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds()
        
        logger.info(
            f"Database optimization completed in {results['duration_seconds']:.2f} seconds"
        )
        
        return results
    
    async def create_indexes(self) -> bool:
        """
        Create recommended indexes for performance.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Creating recommended indexes...")
            
            indexes = [
                # Candles
                "CREATE INDEX IF NOT EXISTS idx_candles_symbol_timeframe ON candles(symbol, timeframe)",
                "CREATE INDEX IF NOT EXISTS idx_candles_timestamp ON candles(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_candles_exchange_symbol ON candles(exchange, symbol)",
                
                # Tickers
                "CREATE INDEX IF NOT EXISTS idx_tickers_symbol ON tickers(symbol)",
                "CREATE INDEX IF NOT EXISTS idx_tickers_timestamp ON tickers(timestamp)",
                
                # Trades
                "CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)",
                "CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)",
                
                # Collection logs
                "CREATE INDEX IF NOT EXISTS idx_collection_logs_symbol ON data_collection_logs(symbol)",
                "CREATE INDEX IF NOT EXISTS idx_collection_logs_collected_at ON data_collection_logs(collected_at)",
            ]
            
            for index_sql in indexes:
                await self.db_session.execute(text(index_sql))
            
            await self.db_session.commit()
            
            logger.info("Recommended indexes created successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            await self.db_session.rollback()
            return False
    
    async def get_optimization_stats(self) -> dict:
        """
        Get optimization statistics.
        
        Returns:
            Dictionary with optimization stats
        """
        db_size = await self.get_database_size()
        table_sizes = await self.get_table_sizes()
        
        return {
            "database_size_bytes": db_size,
            "database_size_mb": (db_size or 0) / (1024 * 1024),
            "table_count": len(table_sizes),
            "table_sizes": table_sizes,
            "last_vacuum": self._last_vacuum.isoformat() if self._last_vacuum else None,
            "last_analyze": self._last_analyze.isoformat() if self._last_analyze else None,
        }
    
    async def cleanup_old_logs(self, days_to_keep: int = 30) -> int:
        """
        Clean up old collection logs.
        
        Args:
            days_to_keep: Number of days to keep logs
        
        Returns:
            Number of deleted records
        """
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            result = await self.db_session.execute(
                text("""
                    DELETE FROM data_collection_logs
                    WHERE collected_at < :cutoff_date
                """),
                {"cutoff_date": cutoff_date}
            )
            
            await self.db_session.commit()
            
            deleted_count = result.rowcount or 0
            logger.info(f"Deleted {deleted_count} old collection logs")
            
            return deleted_count
        
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            await self.db_session.rollback()
            return 0
    
    async def run_periodic_optimization(self, interval_hours: int = 24) -> None:
        """
        Run periodic optimization in background.
        
        Args:
            interval_hours: How often to run optimization
        """
        logger.info(f"Starting periodic optimization (every {interval_hours}h)")
        
        while True:
            try:
                await asyncio.sleep(interval_hours * 3600)
                
                # Run optimization
                results = await self.optimize_all()
                
                # Cleanup old logs (once a week)
                if datetime.now(timezone.utc).weekday() == 6:  # Sunday
                    await self.cleanup_old_logs(days_to_keep=30)
                
                logger.info(f"Periodic optimization completed: {results}")
            
            except asyncio.CancelledError:
                logger.info("Periodic optimization cancelled")
                break
            except Exception as e:
                logger.error(f"Error in periodic optimization: {e}")
