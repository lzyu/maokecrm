"""Sales Opportunities API endpoints."""

from datetime import datetime, date

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_session
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import is_admin_or_above

router = APIRouter()


# Stage labels and order
STAGE_ORDER = ['new', 'qualified', 'proposal', 'negotiation', 'won', 'lost']

STAGE_LABELS = {
    'new': '新建',
    'qualified': '已验证',
    'proposal': '报价',
    'negotiation': '谈判',
    'won': '赢单',
    'lost': '输单',
}


class OpportunityCreate(BaseModel):
    customer_id: int
    opportunity_name: str
    expected_amount: float | None = 0
    probability: float | None = None
    stage: str = 'new'
    expected_close_date: str | None = None


class OpportunityUpdate(BaseModel):
    opportunity_name: str | None = None
    expected_amount: float | None = None
    probability: float | None = None
    stage: str | None = None
    expected_close_date: str | None = None


class OpportunityStageUpdate(BaseModel):
    stage: str


class OpportunityResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: str | None
    opportunity_name: str
    expected_amount: float
    probability: float | None
    stage: str
    stage_label: str
    expected_close_date: str | None
    owner_user_id: int
    owner_name: str | None
    created_at: str
    updated_at: str


class OpportunityListResponse(BaseModel):
    items: list[OpportunityResponse]
    total: int
    page: int
    page_size: int


class OpportunityKanbanResponse(BaseModel):
    columns: dict[str, list[OpportunityResponse]]


@router.get("", response_model=OpportunityListResponse)
async def list_opportunities(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: int | None = Query(None),
    stage: str | None = Query(None),
):
    """List sales opportunities."""
    offset = (page - 1) * page_size

    # Build base query
    base_where = "so.deleted_at IS NULL"
    params = {}

    if customer_id:
        base_where += " AND so.customer_id = :customer_id"
        params["customer_id"] = customer_id

    if stage:
        base_where += " AND so.stage = :stage"
        params["stage"] = stage

    # Role-based filtering - sales can only see their own opportunities
    if not is_admin_or_above(current_user.role_name):
        base_where += " AND so.owner_user_id = :owner_user_id"
        params["owner_user_id"] = current_user.id

    # Count query
    count_query = text(f"SELECT COUNT(*) FROM sales_opportunities so WHERE {base_where}")
    result = await session.execute(count_query, params)
    total = result.scalar()

    # Data query
    data_query = text(f"""
        SELECT so.id, so.customer_id, c.name as customer_name, so.opportunity_name,
               so.expected_amount, so.probability, so.stage, so.expected_close_date,
               so.owner_user_id, u.name as owner_name, so.created_at, so.updated_at
        FROM sales_opportunities so
        LEFT JOIN customers c ON so.customer_id = c.id
        LEFT JOIN users u ON so.owner_user_id = u.id
        WHERE {base_where}
        ORDER BY so.created_at DESC
        OFFSET :offset LIMIT :limit
    """)
    params["offset"] = offset
    params["limit"] = page_size

    result = await session.execute(data_query, params)
    rows = result.fetchall()

    items = [
        OpportunityResponse(
            id=row[0],
            customer_id=row[1],
            customer_name=row[2],
            opportunity_name=row[3],
            expected_amount=float(row[4]) if row[4] else 0,
            probability=float(row[5]) if row[5] else None,
            stage=row[6],
            stage_label=STAGE_LABELS.get(row[6], row[6]),
            expected_close_date=row[7].isoformat() if row[7] else None,
            owner_user_id=row[8],
            owner_name=row[9],
            created_at=row[10].isoformat() if row[10] else "",
            updated_at=row[11].isoformat() if row[11] else "",
        )
        for row in rows
    ]

    return OpportunityListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/kanban", response_model=OpportunityKanbanResponse)
async def get_kanban_view(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    customer_id: int | None = Query(None),
):
    """Get opportunities in kanban view format."""
    # Build base query
    base_where = "so.deleted_at IS NULL"
    params = {}

    if customer_id:
        base_where += " AND so.customer_id = :customer_id"
        params["customer_id"] = customer_id

    # Role-based filtering
    if not is_admin_or_above(current_user.role_name):
        base_where += " AND so.owner_user_id = :owner_user_id"
        params["owner_user_id"] = current_user.id

    # Data query
    data_query = text(f"""
        SELECT so.id, so.customer_id, c.name as customer_name, so.opportunity_name,
               so.expected_amount, so.probability, so.stage, so.expected_close_date,
               so.owner_user_id, u.name as owner_name, so.created_at, so.updated_at
        FROM sales_opportunities so
        LEFT JOIN customers c ON so.customer_id = c.id
        LEFT JOIN users u ON so.owner_user_id = u.id
        WHERE {base_where}
        ORDER BY so.created_at DESC
    """)

    result = await session.execute(data_query, params)
    rows = result.fetchall()

    # Group by stage
    columns: dict[str, list[OpportunityResponse]] = {stage: [] for stage in STAGE_ORDER}

    for row in rows:
        stage = row[6]
        opportunity = OpportunityResponse(
            id=row[0],
            customer_id=row[1],
            customer_name=row[2],
            opportunity_name=row[3],
            expected_amount=float(row[4]) if row[4] else 0,
            probability=float(row[5]) if row[5] else None,
            stage=stage,
            stage_label=STAGE_LABELS.get(stage, stage),
            expected_close_date=row[7].isoformat() if row[7] else None,
            owner_user_id=row[8],
            owner_name=row[9],
            created_at=row[10].isoformat() if row[10] else "",
            updated_at=row[11].isoformat() if row[11] else "",
        )
        if stage in columns:
            columns[stage].append(opportunity)

    return OpportunityKanbanResponse(columns=columns)


@router.post("", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    request: OpportunityCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Create a sales opportunity."""
    # Verify customer exists
    customer_query = text("SELECT id, owner_user_id FROM customers WHERE id = :id AND deleted_at IS NULL")
    result = await session.execute(customer_query, {"id": request.customer_id})
    customer = result.fetchone()

    if not customer:
        raise NotFoundException("Customer not found")

    # Check permission
    if not is_admin_or_above(current_user.role_name):
        if customer[1] != current_user.id:
            raise ForbiddenException("You don't have permission to create opportunity for this customer")

    # Validate stage
    if request.stage not in STAGE_ORDER:
        raise ValueError(f"Invalid stage. Must be one of: {', '.join(STAGE_ORDER)}")

    # Calculate probability based on stage if not provided
    probability = request.probability
    if probability is None:
        stage_probabilities = {
            'new': 10,
            'qualified': 25,
            'proposal': 50,
            'negotiation': 75,
            'won': 100,
            'lost': 0,
        }
        probability = stage_probabilities.get(request.stage, 10)

    # Insert opportunity
    insert_query = text("""
        INSERT INTO sales_opportunities
        (customer_id, owner_user_id, opportunity_name, expected_amount, probability, stage, expected_close_date, created_at, updated_at)
        VALUES (:customer_id, :owner_user_id, :opportunity_name, :expected_amount, :probability, :stage, :expected_close_date, NOW(), NOW())
        RETURNING id, created_at, updated_at
    """)
    params = {
        "customer_id": request.customer_id,
        "owner_user_id": current_user.id,
        "opportunity_name": request.opportunity_name,
        "expected_amount": request.expected_amount or 0,
        "probability": probability,
        "stage": request.stage,
        "expected_close_date": request.expected_close_date if request.expected_close_date else None,
    }

    result = await session.execute(insert_query, params)
    row = result.fetchone()

    return OpportunityResponse(
        id=row[0],
        customer_id=request.customer_id,
        customer_name=None,
        opportunity_name=request.opportunity_name,
        expected_amount=request.expected_amount or 0,
        probability=probability,
        stage=request.stage,
        stage_label=STAGE_LABELS.get(request.stage, request.stage),
        expected_close_date=request.expected_close_date,
        owner_user_id=current_user.id,
        owner_name=current_user.name,
        created_at=row[1].isoformat(),
        updated_at=row[2].isoformat(),
    )


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Get a single opportunity by ID."""
    query = text("""
        SELECT so.id, so.customer_id, c.name as customer_name, so.opportunity_name,
               so.expected_amount, so.probability, so.stage, so.expected_close_date,
               so.owner_user_id, u.name as owner_name, so.created_at, so.updated_at
        FROM sales_opportunities so
        LEFT JOIN customers c ON so.customer_id = c.id
        LEFT JOIN users u ON so.owner_user_id = u.id
        WHERE so.id = :id AND so.deleted_at IS NULL
    """)
    result = await session.execute(query, {"id": opportunity_id})
    row = result.fetchone()

    if not row:
        raise NotFoundException("Opportunity not found")

    # Check permission
    if not is_admin_or_above(current_user.role_name):
        if row[8] != current_user.id:
            raise ForbiddenException("You don't have permission to access this opportunity")

    return OpportunityResponse(
        id=row[0],
        customer_id=row[1],
        customer_name=row[2],
        opportunity_name=row[3],
        expected_amount=float(row[4]) if row[4] else 0,
        probability=float(row[5]) if row[5] else None,
        stage=row[6],
        stage_label=STAGE_LABELS.get(row[6], row[6]),
        expected_close_date=row[7].isoformat() if row[7] else None,
        owner_user_id=row[8],
        owner_name=row[9],
        created_at=row[10].isoformat() if row[10] else "",
        updated_at=row[11].isoformat() if row[11] else "",
    )


@router.put("/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    opportunity_id: int,
    request: OpportunityUpdate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Update a sales opportunity."""
    # Check if exists and has permission
    query = text("SELECT owner_user_id FROM sales_opportunities WHERE id = :id AND deleted_at IS NULL")
    result = await session.execute(query, {"id": opportunity_id})
    row = result.fetchone()

    if not row:
        raise NotFoundException("Opportunity not found")

    if not is_admin_or_above(current_user.role_name) and row[0] != current_user.id:
        raise ForbiddenException("You don't have permission to update this opportunity")

    # Build update query
    update_fields = []
    params = {"id": opportunity_id}

    if request.opportunity_name is not None:
        update_fields.append("opportunity_name = :opportunity_name")
        params["opportunity_name"] = request.opportunity_name

    if request.expected_amount is not None:
        update_fields.append("expected_amount = :expected_amount")
        params["expected_amount"] = request.expected_amount

    if request.probability is not None:
        update_fields.append("probability = :probability")
        params["probability"] = request.probability

    if request.stage is not None:
        if request.stage not in STAGE_ORDER:
            raise ValueError(f"Invalid stage. Must be one of: {', '.join(STAGE_ORDER)}")
        update_fields.append("stage = :stage")
        params["stage"] = request.stage

    if request.expected_close_date is not None:
        update_fields.append("expected_close_date = :expected_close_date")
        # Handle empty string as NULL
        params["expected_close_date"] = request.expected_close_date if request.expected_close_date else None

    if update_fields:
        update_fields.append("updated_at = NOW()")
        update_query = text(f"UPDATE sales_opportunities SET {', '.join(update_fields)} WHERE id = :id")
        await session.execute(update_query, params)

    # Fetch updated record
    return await get_opportunity(opportunity_id, current_user, session)


@router.put("/{opportunity_id}/stage", response_model=OpportunityResponse)
async def update_opportunity_stage(
    opportunity_id: int,
    request: OpportunityStageUpdate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Update opportunity stage only."""
    # Check if exists and has permission
    query = text("SELECT owner_user_id FROM sales_opportunities WHERE id = :id AND deleted_at IS NULL")
    result = await session.execute(query, {"id": opportunity_id})
    row = result.fetchone()

    if not row:
        raise NotFoundException("Opportunity not found")

    if not is_admin_or_above(current_user.role_name) and row[0] != current_user.id:
        raise ForbiddenException("You don't have permission to update this opportunity")

    # Validate stage
    if request.stage not in STAGE_ORDER:
        raise ValueError(f"Invalid stage. Must be one of: {', '.join(STAGE_ORDER)}")

    # Update stage
    update_query = text("""
        UPDATE sales_opportunities
        SET stage = :stage, updated_at = NOW()
        WHERE id = :id
    """)
    await session.execute(update_query, {"id": opportunity_id, "stage": request.stage})

    # Handle won/lost - set closed_at
    if request.stage in ('won', 'lost'):
        closed_query = text("UPDATE sales_opportunities SET closed_at = NOW() WHERE id = :id")
        await session.execute(closed_query, {"id": opportunity_id})

    # Fetch updated record
    return await get_opportunity(opportunity_id, current_user, session)


@router.delete("/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_opportunity(
    opportunity_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Delete a sales opportunity."""
    # Check if exists and has permission
    query = text("SELECT owner_user_id FROM sales_opportunities WHERE id = :id AND deleted_at IS NULL")
    result = await session.execute(query, {"id": opportunity_id})
    row = result.fetchone()

    if not row:
        raise NotFoundException("Opportunity not found")

    if not is_admin_or_above(current_user.role_name) and row[0] != current_user.id:
        raise ForbiddenException("You don't have permission to delete this opportunity")

    # Soft delete
    delete_query = text("UPDATE sales_opportunities SET deleted_at = NOW() WHERE id = :id")
    await session.execute(delete_query, {"id": opportunity_id})
