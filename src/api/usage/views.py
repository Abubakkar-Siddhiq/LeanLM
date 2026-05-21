from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from db.session import get_session
from api.usage.services import UsageAnalytics
from api.usage.schemas import (
    UsageSummaryResponse,
    UsageByModelItem,
    UsageByTaskTypeItem,
    RecentUsageItem,
)


router = APIRouter()
usage_analytics = UsageAnalytics()


@router.get("/usage/summary", response_model=UsageSummaryResponse, tags=["usage"])
def get_usage_summary(
    session: Session = Depends(get_session),
):
    return usage_analytics.get_summary(session)


@router.get("/usage/by-model", response_model=list[UsageByModelItem], tags=["usage"])
def get_usage_by_model(
    session: Session = Depends(get_session),
):
    return usage_analytics.get_usage_by_model(session)


@router.get("/usage/by-task-type", response_model=list[UsageByTaskTypeItem], tags=["usage"])
def get_usage_by_task_type(
    session: Session = Depends(get_session),
):
    return usage_analytics.get_usage_by_task_type(session)


@router.get("/usage/recent", response_model=list[RecentUsageItem], tags=["usage"])
def get_recent_usage(
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    return usage_analytics.get_recent_usage(session, limit=limit)
