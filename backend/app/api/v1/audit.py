"""Audit Logs API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_session
from app.core.permissions import is_admin_or_above
from app.core.exceptions import ForbiddenException

router = APIRouter()


class AuditLogResponse(BaseModel):
    """Audit log response schema."""

    id: int
    actor_user_id: int | None
    actor_name: str | None
    action: str
    resource_type: str
    resource_id: int | None
    before_data: dict | None
    after_data: dict | None
    ip_address: str | None
    user_agent: str | None
    created_at: str


class AuditLogListResponse(BaseModel):
    """Audit log list response schema."""

    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int


class AuditLogStats(BaseModel):
    """Audit log statistics."""

    total_logs: int
    action_counts: dict[str, int]
    resource_type_counts: dict[str, int]


# Action labels for display
ACTION_LABELS = {
    "create": "创建",
    "update": "更新",
    "delete": "删除",
    "login": "登录",
    "logout": "登出",
    "export": "导出",
    "import": "导入",
    "status_change": "状态变更",
}

RESOURCE_TYPE_LABELS = {
    "customer": "客户",
    "user": "用户",
    "followup": "跟进记录",
    "service_record": "服务记录",
    "opportunity": "销售机会",
    "reminder": "提醒",
    "tag": "标签",
    "import_batch": "导入批次",
}


@router.get("/logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    actor_user_id: int | None = Query(None, description="Filter by actor user ID"),
    action: str | None = Query(None, description="Filter by action type"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    resource_id: int | None = Query(None, description="Filter by resource ID"),
    start_time: str | None = Query(None, description="Filter by start time (ISO format)"),
    end_time: str | None = Query(None, description="Filter by end time (ISO format)"),
):
    """
    List audit logs with filtering and pagination.
    Only admin and above can access audit logs.
    """
    if not is_admin_or_above(current_user.role_name):
        raise ForbiddenException("Only admin can access audit logs")

    offset = (page - 1) * page_size

    # Build where clause
    where_clauses = ["1=1"]
    params = {}

    if actor_user_id:
        where_clauses.append("al.actor_user_id = :actor_user_id")
        params["actor_user_id"] = actor_user_id

    if action:
        where_clauses.append("al.action = :action")
        params["action"] = action

    if resource_type:
        where_clauses.append("al.resource_type = :resource_type")
        params["resource_type"] = resource_type

    if resource_id:
        where_clauses.append("al.resource_id = :resource_id")
        params["resource_id"] = resource_id

    if start_time:
        where_clauses.append("al.created_at >= :start_time")
        params["start_time"] = start_time

    if end_time:
        where_clauses.append("al.created_at <= :end_time")
        params["end_time"] = end_time

    where_clause = " AND ".join(where_clauses)

    # Count query
    count_query = f"""
        SELECT COUNT(*)
        FROM audit_logs al
        WHERE {where_clause}
    """
    result = await session.execute(count_query, params)
    total = result.scalar()

    # Data query with user join for actor name
    data_query = f"""
        SELECT al.id, al.actor_user_id, u.name as actor_name, al.action,
               al.resource_type, al.resource_id, al.before_data, al.after_data,
               al.ip_address::text, al.user_agent, al.created_at
        FROM audit_logs al
        LEFT JOIN users u ON al.actor_user_id = u.id
        WHERE {where_clause}
        ORDER BY al.created_at DESC
        OFFSET :offset LIMIT :limit
    """
    params["offset"] = offset
    params["limit"] = page_size

    result = await session.execute(data_query, params)
    rows = result.fetchall()

    items = [
        AuditLogResponse(
            id=row[0],
            actor_user_id=row[1],
            actor_name=row[2],
            action=row[3],
            resource_type=row[4],
            resource_id=row[5],
            before_data=row[6],
            after_data=row[7],
            ip_address=row[8],
            user_agent=row[9],
            created_at=row[10].isoformat() if row[10] else "",
        )
        for row in rows
    ]

    return AuditLogListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=AuditLogStats)
async def get_audit_log_stats(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    start_time: str | None = Query(None, description="Filter by start time (ISO format)"),
    end_time: str | None = Query(None, description="Filter by end time (ISO format)"),
):
    """
    Get audit log statistics.
    Only admin and above can access audit log stats.
    """
    if not is_admin_or_above(current_user.role_name):
        raise ForbiddenException("Only admin can access audit logs")

    # Build where clause
    where_clauses = ["1=1"]
    params = {}

    if start_time:
        where_clauses.append("created_at >= :start_time")
        params["start_time"] = start_time

    if end_time:
        where_clauses.append("created_at <= :end_time")
        params["end_time"] = end_time

    where_clause = " AND ".join(where_clauses)

    # Total count
    total_query = f"SELECT COUNT(*) FROM audit_logs WHERE {where_clause}"
    result = await session.execute(total_query, params)
    total_logs = result.scalar()

    # Action counts
    action_query = f"""
        SELECT action, COUNT(*) as cnt
        FROM audit_logs
        WHERE {where_clause}
        GROUP BY action
    """
    result = await session.execute(action_query, params)
    action_counts = {row[0]: row[1] for row in result.fetchall()}

    # Resource type counts
    resource_query = f"""
        SELECT resource_type, COUNT(*) as cnt
        FROM audit_logs
        WHERE {where_clause}
        GROUP BY resource_type
    """
    result = await session.execute(resource_query, params)
    resource_type_counts = {row[0]: row[1] for row in result.fetchall()}

    return AuditLogStats(
        total_logs=total_logs,
        action_counts=action_counts,
        resource_type_counts=resource_type_counts,
    )


@router.get("/actions", response_model=list[dict])
async def list_audit_actions(
    current_user: CurrentUser,
):
    """
    List available audit action types.
    """
    return [
        {"value": k, "label": v}
        for k, v in ACTION_LABELS.items()
    ]


@router.get("/resource-types", response_model=list[dict])
async def list_resource_types(
    current_user: CurrentUser,
):
    """
    List available resource types.
    """
    return [
        {"value": k, "label": v}
        for k, v in RESOURCE_TYPE_LABELS.items()
    ]
