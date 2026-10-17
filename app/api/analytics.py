from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("")
async def get_analytics(db: AsyncSession = Depends(get_db)):
    metrics = await AnalyticsService.get_dashboard_metrics(db)
    return metrics
