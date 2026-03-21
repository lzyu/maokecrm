"""Reminders API endpoints."""

from datetime import datetime

from dateutil import parser as date_parser
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_session
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import is_admin_or_above

router = APIRouter()


def parse_datetime(dt_str: str | None) -> datetime | None:
    """Parse datetime string to datetime object."""
    if not dt_str:
        return None
    if isinstance(dt_str, datetime):
        return dt_str
    return date_parser.parse(dt_str)


class ReminderCreate(BaseModel):
    customer_id: int
    assignee_user_id: int
    reminder_type: str
    reminder_time: str
    priority: str = "medium"
    content: str | None = None


class ReminderUpdate(BaseModel):
    reminder_time: str | None = None
    priority: str | None = None
    content: str | None = None
    status: str | None = None


class ReminderResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: str | None
    created_by: int
    assignee_user_id: int
    assignee_name: str | None
    reminder_type: str
    reminder_time: str
    priority: str
    status: str
    content: str | None
    created_at: str


class ReminderListResponse(BaseModel):
    items: list[ReminderResponse]
    total: int
    page: int
    page_size: int


reminder_type_labels = {
    "followup": "跟进提醒",
    "renewal": "续费提醒",
    "progress_check": "进度检查",
    "other": "其他",
}

priority_labels = {
    "low": "低",
    "medium": "中",
    "high": "高",
}


@router.get("", response_model=ReminderListResponse)
async def list_reminders(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    priority: str | None = Query(None),
):
    """List reminders."""
    offset = (page - 1) * page_size

    base_where = "sr.deleted_at IS NULL"
    params = {}

    # Non-admin only see their assigned reminders
    if not is_admin_or_above(current_user.role_name):
        base_where += " AND sr.assignee_user_id = :user_id"
        params["user_id"] = current_user.id

    if status:
        base_where += " AND sr.status = :status"
        params["status"] = status

    if priority:
        base_where += " AND sr.priority = :priority"
        params["priority"] = priority

    # Count
    count_query = text(f"SELECT COUNT(*) FROM service_reminders sr WHERE {base_where}")
    result = await session.execute(count_query, params)
    total = result.scalar()

    # Data
    data_query = text(f"""
        SELECT sr.id, sr.customer_id, c.name as customer_name, sr.created_by, sr.assignee_user_id,
               u.name as assignee_name, sr.reminder_type, sr.reminder_time, sr.priority, sr.status, sr.content, sr.created_at
        FROM service_reminders sr
        LEFT JOIN customers c ON sr.customer_id = c.id
        LEFT JOIN users u ON sr.assignee_user_id = u.id
        WHERE {base_where}
        ORDER BY sr.reminder_time ASC
        OFFSET :offset LIMIT :limit
    """)
    params["offset"] = offset
    params["limit"] = page_size

    result = await session.execute(data_query, params)
    rows = result.fetchall()

    items = [
        ReminderResponse(
            id=row[0],
            customer_id=row[1],
            customer_name=row[2],
            created_by=row[3],
            assignee_user_id=row[4],
            assignee_name=row[5],
            reminder_type=row[6],
            reminder_time=row[7].isoformat() if row[7] else "",
            priority=row[8],
            status=row[9],
            content=row[10],
            created_at=row[11].isoformat() if row[11] else "",
        )
        for row in rows
    ]

    return ReminderListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    request: ReminderCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Create a reminder."""
    # Verify customer
    query = text("SELECT id FROM customers WHERE id = :id AND deleted_at IS NULL")
    result = await session.execute(query, {"id": request.customer_id})
    if not result.fetchone():
        raise NotFoundException("Customer not found")

    # Verify assignee
    query = text("SELECT id, name FROM users WHERE id = :id AND deleted_at IS NULL AND status = 'active'")
    result = await session.execute(query, {"id": request.assignee_user_id})
    assignee = result.fetchone()
    if not assignee:
        raise NotFoundException("Assignee not found or inactive")

    # Parse datetime
    reminder_time = parse_datetime(request.reminder_time)

    # Insert
    insert_query = text("""
        INSERT INTO service_reminders (customer_id, created_by, assignee_user_id, reminder_type, reminder_time, priority, content, status, created_at, updated_at)
        VALUES (:customer_id, :created_by, :assignee_user_id, :reminder_type, :reminder_time, :priority, :content, 'pending', NOW(), NOW())
        RETURNING id, created_at
    """)
    params = {
        "customer_id": request.customer_id,
        "created_by": current_user.id,
        "assignee_user_id": request.assignee_user_id,
        "reminder_type": request.reminder_type,
        "reminder_time": reminder_time,
        "priority": request.priority,
        "content": request.content,
    }

    result = await session.execute(insert_query, params)
    row = result.fetchone()

    return ReminderResponse(
        id=row[0],
        customer_id=request.customer_id,
        customer_name=None,
        created_by=current_user.id,
        assignee_user_id=request.assignee_user_id,
        assignee_name=assignee[1],
        reminder_type=request.reminder_type,
        reminder_time=request.reminder_time,
        priority=request.priority,
        status="pending",
        content=request.content,
        created_at=row[1].isoformat(),
    )


@router.put("/{reminder_id}/done", response_model=ReminderResponse)
async def mark_reminder_done(
    reminder_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Mark reminder as done."""
    query = text("SELECT id, assignee_user_id FROM service_reminders WHERE id = :id AND deleted_at IS NULL")
    result = await session.execute(query, {"id": reminder_id})
    row = result.fetchone()

    if not row:
        raise NotFoundException("Reminder not found")

    if not is_admin_or_above(current_user.role_name) and row[1] != current_user.id:
        raise ForbiddenException("You don't have permission to update this reminder")

    # Update
    update_query = text("UPDATE service_reminders SET status = 'done', done_at = NOW(), updated_at = NOW() WHERE id = :id")
    await session.execute(update_query, {"id": reminder_id})

    # Fetch updated
    data_query = text("""
        SELECT sr.id, sr.customer_id, c.name, sr.created_by, sr.assignee_user_id, u.name,
               sr.reminder_type, sr.reminder_time, sr.priority, sr.status, sr.content, sr.created_at
        FROM service_reminders sr
        LEFT JOIN customers c ON sr.customer_id = c.id
        LEFT JOIN users u ON sr.assignee_user_id = u.id
        WHERE sr.id = :id
    """)
    result = await session.execute(data_query, {"id": reminder_id})
    row = result.fetchone()

    return ReminderResponse(
        id=row[0],
        customer_id=row[1],
        customer_name=row[2],
        created_by=row[3],
        assignee_user_id=row[4],
        assignee_name=row[5],
        reminder_type=row[6],
        reminder_time=row[7].isoformat() if row[7] else "",
        priority=row[8],
        status=row[9],
        content=row[10],
        created_at=row[11].isoformat() if row[11] else "",
    )


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Delete a reminder."""
    query = text("SELECT id, assignee_user_id FROM service_reminders WHERE id = :id AND deleted_at IS NULL")
    result = await session.execute(query, {"id": reminder_id})
    row = result.fetchone()

    if not row:
        raise NotFoundException("Reminder not found")

    if not is_admin_or_above(current_user.role_name) and row[1] != current_user.id:
        raise ForbiddenException("You don't have permission to delete this reminder")

    # Soft delete
    delete_query = text("UPDATE service_reminders SET deleted_at = NOW() WHERE id = :id")
    await session.execute(delete_query, {"id": reminder_id})
