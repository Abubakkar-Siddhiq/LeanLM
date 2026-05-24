from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from db.session import get_session
from api.auth.dependencies import get_current_user
from db.models import User
from api.usage.schemas import (
    UsageSummaryResponse,
    UsageByModelItem,
    UsageByTaskTypeItem,
    RecentUsageItem,
)
from api.usage.services import UsageAnalytics


router = APIRouter()
analytics = UsageAnalytics()


@router.get(
    "/usage/summary",
    response_model=UsageSummaryResponse,
    tags=["usage"],
)
def get_usage_summary(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return analytics.get_summary(session, current_user.id)


@router.get(
    "/usage/by-model",
    response_model=list[UsageByModelItem],
    tags=["usage"],
)
def get_usage_by_model(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return analytics.get_usage_by_model(session, current_user.id)


@router.get(
    "/usage/by-task-type",
    response_model=list[UsageByTaskTypeItem],
    tags=["usage"],
)
def get_usage_by_task_type(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return analytics.get_usage_by_task_type(session, current_user.id)


@router.get(
    "/usage/recent",
    response_model=list[RecentUsageItem],
    tags=["usage"],
)
def get_recent_usage(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
):
    return analytics.get_recent_usage(session, current_user.id, limit=limit)
