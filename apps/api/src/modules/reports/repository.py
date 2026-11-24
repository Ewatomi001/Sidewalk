from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import Select, asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.reports.models import Report

ReportSortField = Literal["created_at", "-created_at", "updated_at", "-updated_at"]

SORT_CLAUSES = {
    "created_at": asc(Report.created_at),
    "-created_at": desc(Report.created_at),
    "updated_at": asc(Report.updated_at),
    "-updated_at": desc(Report.updated_at),
}


def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class ReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _apply_filters(
        self,
        stmt: Select,
        *,
        category: str | None = None,
        status: str | None = None,
        user_id: UUID | None = None,
        q: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> Select:
        if category is not None:
            stmt = stmt.where(Report.category == category)
        if status is not None:
            stmt = stmt.where(Report.status == status)
        if user_id is not None:
            stmt = stmt.where(Report.user_id == user_id)
        if q is not None and q.strip():
            pattern = f"%{_escape_like(q.strip())}%"
            stmt = stmt.where(
                or_(
                    Report.title.ilike(pattern, escape="\\"),
                    Report.address.ilike(pattern, escape="\\"),
                )
            )
        if created_from is not None:
            stmt = stmt.where(Report.created_at >= created_from)
        if created_to is not None:
            stmt = stmt.where(Report.created_at <= created_to)
        return stmt

    async def list_reports(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        category: str | None = None,
        status: str | None = None,
        user_id: UUID | None = None,
        q: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        sort: ReportSortField = "-created_at",
    ) -> tuple[list[Report], int]:
        order_expr = SORT_CLAUSES.get(sort)
        if order_expr is None:
            raise ValueError(f"Unsupported sort option: {sort}")

        base_stmt = self._apply_filters(
            select(Report),
            category=category,
            status=status,
            user_id=user_id,
            q=q,
            created_from=created_from,
            created_to=created_to,
        )

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar_one()

        items_stmt = (
            base_stmt
            .order_by(order_expr, desc(Report.id))
            .limit(limit)
            .offset(offset)
        )
        items = list((await self.session.execute(items_stmt)).scalars().all())
        return items, total
