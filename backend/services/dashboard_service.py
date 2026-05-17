"""
Analytics dashboard aggregation service.
Read-only. Does not call LLM or perform any system action.
"""
from __future__ import annotations
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.storage_service import get_dashboard_summary

logger = logging.getLogger(__name__)


async def get_summary(session: AsyncSession) -> dict:
    return await get_dashboard_summary(session)
