from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.modules.reports.repository import ReportRepository, ReportSortField
from src.modules.reports.schemas import ReportListResponse, ReportRead

router = APIRouter(prefix="/reports", tags=["reports"])


def get_report_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ReportRepository:
    return ReportRepository(session)


@router.get(
    "",
    response_model=ReportListResponse,
    summary="List reports with filtering, text search, date range, and sorting",
)
async def list_reports(
    repo: Annotated[ReportRepository, Depends(get_report_repository)],
    category: Annotated[str | None, Query(description="Filter by report category")] = None,
    status_filter: Annotated[
        str | None,
        Query(alias="status", description="Filter by report status"),
    ] = None,
    user_id: Annotated[UUID | None, Query(description="Filter by author user ID")] = None,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=200,
            description="Case-insensitive search across report title and address",
        ),
    ] = None,
    created_from: Annotated[
        datetime | None,
        Query(description="Include reports created at or after this ISO-8601 timestamp"),
    ] = None,
    created_to: Annotated[
        datetime | None,
        Query(description="Include reports created at or before this ISO-8601 timestamp"),
    ] = None,
    sort: Annotated[
        ReportSortField,
        Query(
            description="Sort order (whitelisted: created_at, -created_at, updated_at, -updated_at)",
        ),
    ] = "-created_at",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ReportListResponse:
    if created_from is not None and created_to is not None and created_from > created_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="created_from must be less than or equal to created_to",
        )

    items, total = await repo.list_reports(
        limit=limit,
        offset=offset,
        category=category,
        status=status_filter,
        user_id=user_id,
        q=q,
        created_from=created_from,
        created_to=created_to,
        sort=sort,
    )
    return ReportListResponse(
        items=[ReportRead.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )
