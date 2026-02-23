"""Market Data API - Management of data collection."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.market_data import (
    MonitoredPair,
    Candle,
    Ticker,
    DataCollectionLog,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/market-data", tags=["Market Data"])


# === Request/Response Models ===

class MonitoredPairRequest(BaseModel):
    """Request to add/update monitored pair."""
    symbol: str = Field(..., description="Trading pair symbol (e.g., 'BTCUSDT')")
    timeframes: List[str] = Field(..., description="List of timeframes (e.g., ['1h', '4h', '1d'])")
    is_active: bool = Field(default=True, description="Whether to actively collect data")


class MonitoredPairResponse(BaseModel):
    """Monitored pair information."""
    id: int
    exchange: str
    symbol: str
    timeframes: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_data_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CandleResponse(BaseModel):
    """Candle data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class CollectionStatsResponse(BaseModel):
    """Data collection statistics."""
    exchange: str
    total_monitored_pairs: int
    active_pairs: int
    total_candles: int
    date_range_from: Optional[datetime] = None
    date_range_to: Optional[datetime] = None
    last_collection: Optional[datetime] = None


class BackfillRequest(BaseModel):
    """Request to backfill historical data."""
    symbol: str
    timeframes: List[str]
    days_to_backfill: int = Field(default=30, ge=1, le=365)


# === Helpers ===

async def get_current_exchange() -> str:
    """Get current exchange name from settings."""
    # TODO: Get from settings or app state
    return "binance"


# === Monitored Pairs ===

@router.get("/monitored-pairs", response_model=List[MonitoredPairResponse])
async def get_monitored_pairs(
    active_only: bool = Query(False, description="Return only active pairs"),
    exchange: str = Depends(get_current_exchange),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all monitored trading pairs.
    
    Returns list of pairs that are being tracked for data collection.
    Historical data is preserved even when monitoring stops.
    """
    query = select(MonitoredPair).where(MonitoredPair.exchange == exchange)
    
    if active_only:
        query = query.where(MonitoredPair.is_active == 1)
    
    result = await db.execute(query.order_by(MonitoredPair.symbol))
    pairs = result.scalars().all()
    
    return [
        MonitoredPairResponse(
            id=p.id,
            exchange=p.exchange,
            symbol=p.symbol,
            timeframes=p.timeframes.split(",") if p.timeframes else [],
            is_active=bool(p.is_active),
            created_at=p.created_at,
            updated_at=p.updated_at,
            last_data_at=p.last_data_at,
        )
        for p in pairs
    ]


@router.post("/monitored-pairs", response_model=MonitoredPairResponse)
async def add_monitored_pair(
    request: MonitoredPairRequest,
    exchange: str = Depends(get_current_exchange),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a trading pair to monitored list.
    
    Starts collecting candle data for the specified symbol and timeframes.
    Data will be collected continuously in the background.
    """
    # Check if already exists
    result = await db.execute(
        select(MonitoredPair).where(
            and_(
                MonitoredPair.exchange == exchange,
                MonitoredPair.symbol == request.symbol,
            )
        )
    )
    
    pair = result.scalar_one_or_none()
    
    if pair:
        # Update existing
        pair.timeframes = ",".join(request.timeframes)
        pair.is_active = 1 if request.is_active else 0
        pair.updated_at = datetime.utcnow()
    else:
        # Create new
        pair = MonitoredPair(
            exchange=exchange,
            symbol=request.symbol,
            timeframes=",".join(request.timeframes),
            is_active=1 if request.is_active else 0,
        )
        db.add(pair)
    
    await db.commit()
    await db.refresh(pair)
    
    logger.info(f"Added monitored pair: {exchange}:{request.symbol}")
    
    return MonitoredPairResponse(
        id=pair.id,
        exchange=pair.exchange,
        symbol=pair.symbol,
        timeframes=pair.timeframes.split(",") if pair.timeframes else [],
        is_active=bool(pair.is_active),
        created_at=pair.created_at,
        updated_at=pair.updated_at,
        last_data_at=pair.last_data_at,
    )


@router.delete("/monitored-pairs/{symbol}")
async def remove_monitored_pair(
    symbol: str,
    exchange: str = Depends(get_current_exchange),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a pair from monitored list.
    
    NOTE: This does NOT delete historical data!
    It only stops future data collection.
    """
    result = await db.execute(
        select(MonitoredPair).where(
            and_(
                MonitoredPair.exchange == exchange,
                MonitoredPair.symbol == symbol,
            )
        )
    )
    
    pair = result.scalar_one_or_none()
    
    if not pair:
        raise HTTPException(status_code=404, detail=f"Pair {symbol} not found")
    
    # Deactivate (don't delete)
    pair.is_active = 0
    pair.updated_at = datetime.utcnow()
    
    await db.commit()
    
    logger.info(f"Removed monitored pair: {exchange}:{symbol} (data preserved)")
    
    return {"message": f"Pair {symbol} removed from monitoring (historical data preserved)"}


@router.post("/monitored-pairs/{symbol}/resume")
async def resume_monitored_pair(
    symbol: str,
    exchange: str = Depends(get_current_exchange),
    db: AsyncSession = Depends(get_db),
):
    """
    Resume monitoring for a previously monitored pair.
    
    Will automatically backfill missing data.
    """
    result = await db.execute(
        select(MonitoredPair).where(
            and_(
                MonitoredPair.exchange == exchange,
                MonitoredPair.symbol == symbol,
            )
        )
    )
    
    pair = result.scalar_one_or_none()
    
    if not pair:
        raise HTTPException(status_code=404, detail=f"Pair {symbol} not found")
    
    # Reactivate
    pair.is_active = 1
    pair.updated_at = datetime.utcnow()
    
    await db.commit()
    
    logger.info(f"Resumed monitoring for: {exchange}:{symbol}")
    
    return {"message": f"Monitoring resumed for {symbol}, backfill will start"}


# === Candle Data ===

@router.get("/candles/{symbol}", response_model=List[CandleResponse])
async def get_candles(
    symbol: str,
    timeframe: str = Query(..., description="Candle timeframe"),
    limit: int = Query(100, ge=1, le=1000, description="Number of candles"),
    exchange: str = Depends(get_current_exchange),
    db: AsyncSession = Depends(get_db),
):
    """
    Get historical candle data.
    
    Returns candles from the database. Data is collected continuously
    for monitored pairs.
    """
    result = await db.execute(
        select(Candle)
        .where(
            and_(
                Candle.exchange == exchange,
                Candle.symbol == symbol,
                Candle.timeframe == timeframe,
            )
        )
        .order_by(Candle.timestamp.desc())
        .limit(limit)
    )
    
    candles = result.scalars().all()
    
    return [
        CandleResponse(
            timestamp=c.timestamp,
            open=c.open,
            high=c.high,
            low=c.low,
            close=c.close,
            volume=c.volume,
        )
        for c in reversed(candles)
    ]


@router.get("/candles/{symbol}/count")
async def get_candle_count(
    symbol: str,
    timeframe: Optional[str] = Query(None, description="Filter by timeframe"),
    exchange: str = Depends(get_current_exchange),
    db: AsyncSession = Depends(get_db),
):
    """
    Get total number of candles in database.
    """
    query = select(func.count(Candle.id)).where(
        and_(
            Candle.exchange == exchange,
            Candle.symbol == symbol,
        )
    )
    
    if timeframe:
        query = query.where(Candle.timeframe == timeframe)
    
    result = await db.execute(query)
    count = result.scalar()
    
    return {"symbol": symbol, "timeframe": timeframe, "count": count or 0}


# === Statistics ===

@router.get("/stats", response_model=CollectionStatsResponse)
async def get_collection_stats(
    exchange: str = Depends(get_current_exchange),
    db: AsyncSession = Depends(get_db),
):
    """
    Get data collection statistics.
    """
    # Total monitored pairs
    total_result = await db.execute(
        select(func.count(MonitoredPair.id)).where(MonitoredPair.exchange == exchange)
    )
    total_pairs = total_result.scalar() or 0
    
    # Active pairs
    active_result = await db.execute(
        select(func.count(MonitoredPair.id)).where(
            and_(
                MonitoredPair.exchange == exchange,
                MonitoredPair.is_active == 1,
            )
        )
    )
    active_pairs = active_result.scalar() or 0
    
    # Total candles
    candles_result = await db.execute(
        select(func.count(Candle.id)).where(Candle.exchange == exchange)
    )
    total_candles = candles_result.scalar() or 0
    
    # Date range
    date_range_result = await db.execute(
        select(
            func.min(Candle.timestamp),
            func.max(Candle.timestamp),
        ).where(Candle.exchange == exchange)
    )
    date_range = date_range_result.one()
    
    # Last collection
    last_log_result = await db.execute(
        select(DataCollectionLog.collected_at)
        .where(DataCollectionLog.exchange == exchange)
        .order_by(DataCollectionLog.collected_at.desc())
    )
    last_collection = last_log_result.scalar()
    
    return CollectionStatsResponse(
        exchange=exchange,
        total_monitored_pairs=total_pairs,
        active_pairs=active_pairs,
        total_candles=total_candles,
        date_range_from=date_range[0],
        date_range_to=date_range[1],
        last_collection=last_collection,
    )


# === Collection Logs ===

@router.get("/logs")
async def get_collection_logs(
    limit: int = Query(50, ge=1, le=500),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    status: Optional[str] = Query(None, description="Filter by status (success/error)"),
    exchange: str = Depends(get_current_exchange),
    db: AsyncSession = Depends(get_db),
):
    """
    Get data collection logs.
    """
    query = select(DataCollectionLog).where(DataCollectionLog.exchange == exchange)
    
    if symbol:
        query = query.where(DataCollectionLog.symbol == symbol)
    
    if status:
        query = query.where(DataCollectionLog.status == status)
    
    query = query.order_by(DataCollectionLog.collected_at.desc()).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return [
        {
            "id": log.id,
            "exchange": log.exchange,
            "symbol": log.symbol,
            "timeframe": log.timeframe,
            "data_type": log.data_type,
            "status": log.status,
            "records_collected": log.records_collected,
            "error_message": log.error_message,
            "data_from": log.data_from,
            "data_to": log.data_to,
            "collected_at": log.collected_at,
        }
        for log in logs
    ]


# === Backfill ===

@router.post("/backfill")
async def backfill_data(
    request: BackfillRequest,
    exchange: str = Depends(get_current_exchange),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger backfill of historical data.
    
    This will fetch historical candles from the exchange and save them to database.
    Useful when resuming monitoring or initializing a new pair.
    
    Note: This is an asynchronous operation. Check logs for progress.
    """
    # Validate symbol exists as monitored pair
    result = await db.execute(
        select(MonitoredPair).where(
            and_(
                MonitoredPair.exchange == exchange,
                MonitoredPair.symbol == request.symbol,
            )
        )
    )
    
    pair = result.scalar_one_or_none()
    
    if not pair:
        raise HTTPException(
            status_code=404,
            detail=f"Pair {request.symbol} is not monitored. Add it first.",
        )
    
    # Create backfill task
    # TODO: Implement actual backfill logic in a background task
    # For now, just log the request
    
    logger.info(
        f"Backfill requested for {exchange}:{request.symbol} "
        f"timeframes={request.timeframes} days={request.days_to_backfill}"
    )
    
    return {
        "message": "Backfill initiated",
        "symbol": request.symbol,
        "timeframes": request.timeframes,
        "days": request.days_to_backfill,
        "status": "pending",
    }


# === Database Optimization ===

@router.post("/optimize")
async def optimize_database(
    run_vacuum: bool = Query(True, description="Run VACUUM"),
    run_analyze: bool = Query(True, description="Run ANALYZE"),
    db: AsyncSession = Depends(get_db),
):
    """
    Optimize database performance.
    
    Operations:
    - VACUUM: Reclaim disk space
    - ANALYZE: Update query statistics
    - Integrity check
    """
    from app.services.database_optimizer import DatabaseOptimizer
    
    optimizer = DatabaseOptimizer(db)
    
    results = {
        "vacuum": False,
        "analyze": False,
        "integrity_check": False,
    }
    
    # Integrity check
    results["integrity_check"] = await optimizer.check_integrity()
    
    # VACUUM
    if run_vacuum:
        results["vacuum"] = await optimizer.vacuum()
    
    # ANALYZE
    if run_analyze:
        results["analyze"] = await optimizer.analyze()
    
    return {
        "message": "Database optimization completed",
        "results": results,
    }


@router.get("/optimization/stats")
async def get_optimization_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get database optimization statistics.
    """
    from app.services.database_optimizer import DatabaseOptimizer
    
    optimizer = DatabaseOptimizer(db)
    stats = await optimizer.get_optimization_stats()
    
    return stats


@router.post("/optimization/cleanup-logs")
async def cleanup_old_logs(
    days_to_keep: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """
    Clean up old collection logs.
    
    Args:
        days_to_keep: Number of days to keep
    """
    from app.services.database_optimizer import DatabaseOptimizer
    
    optimizer = DatabaseOptimizer(db)
    deleted_count = await optimizer.cleanup_old_logs(days_to_keep)
    
    return {
        "message": f"Deleted {deleted_count} old collection logs",
        "deleted_count": deleted_count,
        "days_to_keep": days_to_keep,
    }
