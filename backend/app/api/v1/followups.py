"""Followups API endpoints."""

from datetime import datetime
from dateutil import parser as date_parser

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_session
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import is_admin_or_above
from app.models.customer import Customer
from app.models.user import User

router = APIRouter()


def parse_datetime(dt_str: str | None) -> datetime | None:
    """Parse datetime string to datetime object."""
    if not dt_str:
        return None
    if isinstance(dt_str, datetime):
        return dt_str
    return date_parser.parse(dt_str)


class FollowupCreate(BaseModel):
    customer_id: int
    followup_time: str
    contact_method: str
    content: str
    result: str | None = None
    next_action_time: str | None = None

    class Config:
        # Allow both string and datetime formats
        json_schema_extra = {
            "example": {
                "customer_id": 1,
                "followup_time": "2026-03-21T10:00:00",
                "contact_method": "phone",
                "content": "跟进内容",
                "result": "contacted",
                "next_action_time": None
            }
        }


class FollowupUpdate(BaseModel):
    followup_time: str | None = None
    contact_method: str | None = None
    content: str | None = None
    result: str | None = None
    next_action_time: str | None = None


class FollowupResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: str | None
    sales_id: int
    sales_name: str | None
    followup_time: str
    contact_method: str
    content: str
    result: str | None
    next_action_time: str | None
    created_at: str


class FollowupListResponse(BaseModel):
    items: list[FollowupResponse]
    total: int
    page: int
    page_size: int


@router.get("", response_model=FollowupListResponse)
async def list_followups(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: int | None = Query(None),
):
    """List followups."""
    # Use raw SQL for now since model not defined
    offset = (page - 1) * page_size

    # Build base query
    base_where = "sf.deleted_at IS NULL"
    params = {}

    if customer_id:
        base_where += " AND sf.customer_id = :customer_id"
        params["customer_id"] = customer_id

    # Role-based filtering - sales can only see their own followups
    if not is_admin_or_above(current_user.role_name):
        base_where += " AND sf.sales_id = :sales_id"
        params["sales_id"] = current_user.id

    # Count query
    count_query = text(f"SELECT COUNT(*) FROM sales_followups sf WHERE {base_where}")
    result = await session.execute(count_query, params)
    total = result.scalar()

    # Data query
    data_query = text(f"""
        SELECT sf.id, sf.customer_id, c.name as customer_name, sf.sales_id, u.name as sales_name,
               sf.followup_time, sf.contact_method, sf.content, sf.result, sf.next_action_time, sf.created_at
        FROM sales_followups sf
        LEFT JOIN customers c ON sf.customer_id = c.id
        LEFT JOIN users u ON sf.sales_id = u.id
        WHERE {base_where}
        ORDER BY sf.followup_time DESC
        OFFSET :offset LIMIT :limit
    """)
    params["offset"] = offset
    params["limit"] = page_size

    result = await session.execute(data_query, params)
    rows = result.fetchall()

    items = [
        FollowupResponse(
            id=row[0],
            customer_id=row[1],
            customer_name=row[2],
            sales_id=row[3],
            sales_name=row[4],
            followup_time=row[5].isoformat() if row[5] else "",
            contact_method=row[6],
            content=row[7],
            result=row[8],
            next_action_time=row[9].isoformat() if row[9] else None,
            created_at=row[10].isoformat() if row[10] else "",
        )
        for row in rows
    ]

    return FollowupListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=FollowupResponse, status_code=status.HTTP_201_CREATED)
async def create_followup(
    request: FollowupCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Create a followup."""
    # Verify customer exists
    customer_query = text("SELECT id, owner_user_id FROM customers WHERE id = :id AND deleted_at IS NULL")
    result = await session.execute(customer_query, {"id": request.customer_id})
    customer = result.fetchone()

    if not customer:
        raise NotFoundException("Customer not found")

    # Check permission
    if not is_admin_or_above(current_user.role_name):
        if customer[1] != current_user.id:
            raise ForbiddenException("You don't have permission to add followup to this customer")

    # Insert followup
    followup_time = parse_datetime(request.followup_time)
    next_action_time = parse_datetime(request.next_action_time)

    insert_query = text("""
        INSERT INTO sales_followups (customer_id, sales_id, followup_time, contact_method, content, result, next_action_time, created_at, updated_at)
        VALUES (:customer_id, :sales_id, :followup_time, :contact_method, :content, :result, :next_action_time, NOW(), NOW())
        RETURNING id, created_at
    """)
    params = {
        "customer_id": request.customer_id,
        "sales_id": current_user.id,
        "followup_time": followup_time,
        "contact_method": request.contact_method,
        "content": request.content,
        "result": request.result,
        "next_action_time": next_action_time,
    }

    result = await session.execute(insert_query, params)
    row = result.fetchone()

    # Update customer last_followup_at
    update_query = text("UPDATE customers SET last_followup_at = :time WHERE id = :id")
    await session.execute(update_query, {"time": followup_time, "id": request.customer_id})

    return FollowupResponse(
        id=row[0],
        customer_id=request.customer_id,
        customer_name=None,
        sales_id=current_user.id,
        sales_name=current_user.name,
        followup_time=request.followup_time,
        contact_method=request.contact_method,
        content=request.content,
        result=request.result,
        next_action_time=request.next_action_time,
        created_at=row[1].isoformat(),
    )


@router.delete("/{followup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_followup(
    followup_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Delete a followup."""
    # Check if exists and has permission
    query = text("SELECT sales_id FROM sales_followups WHERE id = :id AND deleted_at IS NULL")
    result = await session.execute(query, {"id": followup_id})
    row = result.fetchone()

    if not row:
        raise NotFoundException("Followup not found")

    if not is_admin_or_above(current_user.role_name) and row[0] != current_user.id:
        raise ForbiddenException("You don't have permission to delete this followup")

    # Soft delete
    delete_query = text("UPDATE sales_followups SET deleted_at = NOW() WHERE id = :id")
    await session.execute(delete_query, {"id": followup_id})
