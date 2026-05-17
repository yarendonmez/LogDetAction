"""
GET /api/dashboard/summary — read-only analytics aggregates.
"""
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session
from backend.services.dashboard_service import get_summary

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/summary")
async def dashboard_summary(session: AsyncSession = Depends(get_session)):
    try:
        data = await get_summary(session)
        return data
    except Exception as exc:
        logger.exception("Dashboard summary error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": True, "code": "DATABASE_ERROR", "message": str(exc)},
        )
