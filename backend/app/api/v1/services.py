"""Services (Consultation) API endpoints."""

from datetime import datetime

from dateutil import parser as date_parser
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_session
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import RoleName

router = APIRouter()


def parse_datetime(dt_str: str | None) -> datetime | None:
    """Parse datetime string to datetime object."""
    if not dt_str:
        return None
    if isinstance(dt_str, datetime):
        return dt_str
    return date_parser.parse(dt_str)


class ServiceRecordCreate(BaseModel):
    customer_id: int
    service_time: str
    service_content: str
    customer_feedback: str | None = None
    satisfaction_score: int | None = None


class ServiceRecordResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: str | None
    consultant_id: int
    consultant_name: str | None
    service_time: str
    service_content: str
    customer_feedback: str | None
    satisfaction_score: int | None
    created_at: str


class ServiceRecordListResponse(BaseModel):
    items: list[ServiceRecordResponse]
    total: int
    page: int
    page_size: int


@router.get("/records", response_model=ServiceRecordListResponse)
async def list_service_records(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: int | None = Query(None),
):
    """List service records."""
    offset = (page - 1) * page_size

    base_where = "sr.deleted_at IS NULL"
    params = {}

    if customer_id:
        base_where += " AND sr.customer_id = :customer_id"
        params["customer_id"] = customer_id

    # Count
    count_query = text(f"SELECT COUNT(*) FROM service_records sr WHERE {base_where}")
    result = await session.execute(count_query, params)
    total = result.scalar()

    # Data
    data_query = text(f"""
        SELECT sr.id, sr.customer_id, c.name as customer_name, sr.consultant_id, u.name as consultant_name,
               sr.service_time, sr.service_content, sr.customer_feedback, sr.satisfaction_score, sr.created_at
        FROM service_records sr
        LEFT JOIN customers c ON sr.customer_id = c.id
        LEFT JOIN users u ON sr.consultant_id = u.id
        WHERE {base_where}
        ORDER BY sr.service_time DESC
        OFFSET :offset LIMIT :limit
    """)
    params["offset"] = offset
    params["limit"] = page_size

    result = await session.execute(data_query, params)
    rows = result.fetchall()

    items = [
        ServiceRecordResponse(
            id=row[0],
            customer_id=row[1],
            customer_name=row[2],
            consultant_id=row[3],
            consultant_name=row[4],
            service_time=row[5].isoformat() if row[5] else "",
            service_content=row[6],
            customer_feedback=row[7],
            satisfaction_score=row[8],
            created_at=row[9].isoformat() if row[9] else "",
        )
        for row in rows
    ]

    return ServiceRecordListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/records", response_model=ServiceRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_service_record(
    request: ServiceRecordCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Create a service record."""
    # Only consultant or admin can create
    if current_user.role_name not in [RoleName.CONSULTANT.value, RoleName.ADMIN.value, RoleName.SUPER_ADMIN.value]:
        raise ForbiddenException("Only consultant or admin can create service records")

    # Verify customer
    query = text("SELECT id FROM customers WHERE id = :id AND deleted_at IS NULL")
    result = await session.execute(query, {"id": request.customer_id})
    if not result.fetchone():
        raise NotFoundException("Customer not found")

    # Parse datetime
    service_time = parse_datetime(request.service_time)

    # Insert
    insert_query = text("""
        INSERT INTO service_records (customer_id, consultant_id, service_time, service_content, customer_feedback, satisfaction_score, created_at, updated_at)
        VALUES (:customer_id, :consultant_id, :service_time, :service_content, :customer_feedback, :satisfaction_score, NOW(), NOW())
        RETURNING id, created_at
    """)
    params = {
        "customer_id": request.customer_id,
        "consultant_id": current_user.id,
        "service_time": service_time,
        "service_content": request.service_content,
        "customer_feedback": request.customer_feedback,
        "satisfaction_score": request.satisfaction_score,
    }

    result = await session.execute(insert_query, params)
    row = result.fetchone()

    return ServiceRecordResponse(
        id=row[0],
        customer_id=request.customer_id,
        customer_name=None,
        consultant_id=current_user.id,
        consultant_name=current_user.name,
        service_time=request.service_time,
        service_content=request.service_content,
        customer_feedback=request.customer_feedback,
        satisfaction_score=request.satisfaction_score,
        created_at=row[1].isoformat(),
    )
