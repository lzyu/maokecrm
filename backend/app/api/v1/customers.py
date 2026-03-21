"""Customers API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_session
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.masking import mask_phone, mask_wechat
from app.core.permissions import RoleName, is_admin_or_above
from app.models.customer import Customer, CustomerRead, CustomerTag, Tag
from app.models.user import User

router = APIRouter()


class CustomerListResponse(BaseModel):
    items: list[CustomerRead]
    total: int
    page: int
    page_size: int


class CustomerCreateRequest(BaseModel):
    name: str
    phone: str | None = None
    wechat: str | None = None
    company_name: str | None = None
    industry: str | None = None
    source_channel: str | None = None
    customer_status: str = "potential"
    owner_user_id: int | None = None
    tag_ids: list[int] = []


class CustomerUpdateRequest(BaseModel):
    name: str | None = None
    phone: str | None = None
    wechat: str | None = None
    company_name: str | None = None
    industry: str | None = None
    source_channel: str | None = None
    customer_status: str | None = None
    owner_user_id: int | None = None
    tag_ids: list[int] | None = None


def apply_masking(customer_read: CustomerRead, role_name: str) -> CustomerRead:
    """Apply data masking for consultant role."""
    if role_name == RoleName.CONSULTANT.value:
        customer_read.phone = mask_phone(customer_read.phone)
        customer_read.wechat = mask_wechat(customer_read.wechat)
    return customer_read


def can_access_all_customers(role_name: str) -> bool:
    """Check if role can access all customers."""
    return is_admin_or_above(role_name)


def can_modify_customer(role_name: str, customer_owner_id: int, current_user_id: int) -> bool:
    """Check if user can modify a specific customer."""
    if is_admin_or_above(role_name):
        return True
    return customer_owner_id == current_user_id


@router.get("", response_model=CustomerListResponse)
async def list_customers(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None),
    customer_status: str | None = Query(None),
    owner_user_id: int | None = Query(None),
    tag_id: int | None = Query(None),
):
    """
    List customers with pagination and filtering.
    """
    # Build base query
    stmt = select(Customer).where(Customer.deleted_at.is_(None))

    # Role-based filtering
    if not can_access_all_customers(current_user.role_name):
        stmt = stmt.where(Customer.owner_user_id == current_user.id)

    # Apply filters
    if keyword:
        stmt = stmt.where(
            or_(
                Customer.name.ilike(f"%{keyword}%"),
                Customer.phone.ilike(f"%{keyword}%"),
                Customer.company_name.ilike(f"%{keyword}%"),
            )
        )

    if customer_status:
        stmt = stmt.where(Customer.customer_status == customer_status)

    if owner_user_id and is_admin_or_above(current_user.role_name):
        stmt = stmt.where(Customer.owner_user_id == owner_user_id)

    if tag_id:
        tag_subquery = select(CustomerTag.customer_id).where(CustomerTag.tag_id == tag_id)
        stmt = stmt.where(Customer.id.in_(tag_subquery))

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar()

    # Paginate
    offset = (page - 1) * page_size
    stmt = stmt.order_by(Customer.created_at.desc()).offset(offset).limit(page_size)

    result = await session.execute(stmt)
    customers = result.scalars().all()

    # Build response
    items = []
    for customer in customers:
        # Get owner info
        owner_stmt = select(User).where(User.id == customer.owner_user_id)
        owner_result = await session.execute(owner_stmt)
        owner = owner_result.scalar_one_or_none()

        # Get tags
        tag_stmt = (
            select(Tag)
            .join(CustomerTag, CustomerTag.tag_id == Tag.id)
            .where(CustomerTag.customer_id == customer.id)
        )
        tag_result = await session.execute(tag_stmt)
        tags = tag_result.scalars().all()

        customer_read = CustomerRead(
            id=customer.id,
            name=customer.name,
            phone=customer.phone,
            wechat=customer.wechat,
            company_name=customer.company_name,
            industry=customer.industry,
            source_channel=customer.source_channel,
            customer_status=customer.customer_status,
            owner_user_id=customer.owner_user_id,
            owner_name=owner.name if owner else None,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
            last_followup_at=customer.last_followup_at,
            tags=[{"id": t.id, "tag_name": t.tag_name, "tag_type": t.tag_type} for t in tags],
        )

        customer_read = apply_masking(customer_read, current_user.role_name)
        items.append(customer_read)

    return CustomerListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer(
    request: CustomerCreateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new customer.
    """
    # Determine owner
    owner_user_id = request.owner_user_id
    if not is_admin_or_above(current_user.role_name):
        owner_user_id = current_user.id
    elif owner_user_id is None:
        owner_user_id = current_user.id

    # Verify owner exists
    owner_stmt = select(User).where(User.id == owner_user_id, User.deleted_at.is_(None))
    owner_result = await session.execute(owner_stmt)
    owner = owner_result.scalar_one_or_none()

    if not owner:
        raise NotFoundException("Owner user not found")

    # Create customer
    customer = Customer(
        name=request.name,
        phone=request.phone,
        wechat=request.wechat,
        company_name=request.company_name,
        industry=request.industry,
        source_channel=request.source_channel,
        customer_status=request.customer_status,
        owner_user_id=owner_user_id,
        created_by=current_user.id,
    )

    session.add(customer)
    await session.commit()
    await session.refresh(customer)

    # Add tags
    if request.tag_ids:
        for tag_id in request.tag_ids:
            customer_tag = CustomerTag(
                customer_id=customer.id,
                tag_id=tag_id,
                created_by=current_user.id
            )
            session.add(customer_tag)
        await session.commit()

    # Get tags for response
    tag_stmt = (
        select(Tag)
        .join(CustomerTag, CustomerTag.tag_id == Tag.id)
        .where(CustomerTag.customer_id == customer.id)
    )
    tag_result = await session.execute(tag_stmt)
    tags = tag_result.scalars().all()

    return CustomerRead(
        id=customer.id,
        name=customer.name,
        phone=customer.phone,
        wechat=customer.wechat,
        company_name=customer.company_name,
        industry=customer.industry,
        source_channel=customer.source_channel,
        customer_status=customer.customer_status,
        owner_user_id=customer.owner_user_id,
        owner_name=owner.name,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
        last_followup_at=customer.last_followup_at,
        tags=[{"id": t.id, "tag_name": t.tag_name, "tag_type": t.tag_type} for t in tags],
    )


@router.get("/{customer_id}", response_model=CustomerRead)
async def get_customer(
    customer_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """
    Get customer by ID.
    """
    stmt = select(Customer).where(Customer.id == customer_id, Customer.deleted_at.is_(None))
    result = await session.execute(stmt)
    customer = result.scalar_one_or_none()

    if not customer:
        raise NotFoundException("Customer not found")

    # Check permission
    if not can_access_all_customers(current_user.role_name):
        if customer.owner_user_id != current_user.id:
            raise ForbiddenException("You don't have access to this customer")

    # Get owner info
    owner_stmt = select(User).where(User.id == customer.owner_user_id)
    owner_result = await session.execute(owner_stmt)
    owner = owner_result.scalar_one_or_none()

    # Get tags
    tag_stmt = (
        select(Tag)
        .join(CustomerTag, CustomerTag.tag_id == Tag.id)
        .where(CustomerTag.customer_id == customer.id)
    )
    tag_result = await session.execute(tag_stmt)
    tags = tag_result.scalars().all()

    customer_read = CustomerRead(
        id=customer.id,
        name=customer.name,
        phone=customer.phone,
        wechat=customer.wechat,
        company_name=customer.company_name,
        industry=customer.industry,
        source_channel=customer.source_channel,
        customer_status=customer.customer_status,
        owner_user_id=customer.owner_user_id,
        owner_name=owner.name if owner else None,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
        last_followup_at=customer.last_followup_at,
        tags=[{"id": t.id, "tag_name": t.tag_name, "tag_type": t.tag_type} for t in tags],
    )

    return apply_masking(customer_read, current_user.role_name)


@router.put("/{customer_id}", response_model=CustomerRead)
async def update_customer(
    customer_id: int,
    request: CustomerUpdateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """
    Update customer by ID.
    """
    stmt = select(Customer).where(Customer.id == customer_id, Customer.deleted_at.is_(None))
    result = await session.execute(stmt)
    customer = result.scalar_one_or_none()

    if not customer:
        raise NotFoundException("Customer not found")

    # Check permission
    if not can_modify_customer(current_user.role_name, customer.owner_user_id, current_user.id):
        raise ForbiddenException("You don't have permission to update this customer")

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    tag_ids = update_data.pop("tag_ids", None)

    for field, value in update_data.items():
        setattr(customer, field, value)

    customer.updated_at = datetime.utcnow()
    customer.updated_by = current_user.id
    session.add(customer)

    # Update tags if provided
    if tag_ids is not None:
        # Remove existing tags
        delete_stmt = select(CustomerTag).where(CustomerTag.customer_id == customer.id)
        existing_result = await session.execute(delete_stmt)
        for ct in existing_result.scalars().all():
            await session.delete(ct)

        # Add new tags
        for tag_id in tag_ids:
            customer_tag = CustomerTag(
                customer_id=customer.id,
                tag_id=tag_id,
                created_by=current_user.id
            )
            session.add(customer_tag)

    await session.commit()
    await session.refresh(customer)

    # Get owner info
    owner_stmt = select(User).where(User.id == customer.owner_user_id)
    owner_result = await session.execute(owner_stmt)
    owner = owner_result.scalar_one_or_none()

    # Get tags
    tag_stmt = (
        select(Tag)
        .join(CustomerTag, CustomerTag.tag_id == Tag.id)
        .where(CustomerTag.customer_id == customer.id)
    )
    tag_result = await session.execute(tag_stmt)
    tags = tag_result.scalars().all()

    return CustomerRead(
        id=customer.id,
        name=customer.name,
        phone=customer.phone,
        wechat=customer.wechat,
        company_name=customer.company_name,
        industry=customer.industry,
        source_channel=customer.source_channel,
        customer_status=customer.customer_status,
        owner_user_id=customer.owner_user_id,
        owner_name=owner.name if owner else None,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
        last_followup_at=customer.last_followup_at,
        tags=[{"id": t.id, "tag_name": t.tag_name, "tag_type": t.tag_type} for t in tags],
    )


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """
    Soft delete customer by ID.
    Only admin+ can delete customers.
    """
    if not is_admin_or_above(current_user.role_name):
        raise ForbiddenException("Only admin can delete customers")

    stmt = select(Customer).where(Customer.id == customer_id, Customer.deleted_at.is_(None))
    result = await session.execute(stmt)
    customer = result.scalar_one_or_none()

    if not customer:
        raise NotFoundException("Customer not found")

    customer.deleted_at = datetime.utcnow()
    session.add(customer)
    await session.commit()


@router.put("/{customer_id}/status", response_model=CustomerRead)
async def update_customer_status(
    customer_id: int,
    status: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """
    Update customer status.
    """
    stmt = select(Customer).where(Customer.id == customer_id, Customer.deleted_at.is_(None))
    result = await session.execute(stmt)
    customer = result.scalar_one_or_none()

    if not customer:
        raise NotFoundException("Customer not found")

    if not can_modify_customer(current_user.role_name, customer.owner_user_id, current_user.id):
        raise ForbiddenException("You don't have permission to update this customer")

    customer.customer_status = status
    customer.updated_at = datetime.utcnow()
    customer.updated_by = current_user.id
    session.add(customer)
    await session.commit()
    await session.refresh(customer)

    # Get owner info
    owner_stmt = select(User).where(User.id == customer.owner_user_id)
    owner_result = await session.execute(owner_stmt)
    owner = owner_result.scalar_one_or_none()

    # Get tags
    tag_stmt = (
        select(Tag)
        .join(CustomerTag, CustomerTag.tag_id == Tag.id)
        .where(CustomerTag.customer_id == customer.id)
    )
    tag_result = await session.execute(tag_stmt)
    tags = tag_result.scalars().all()

    return CustomerRead(
        id=customer.id,
        name=customer.name,
        phone=customer.phone,
        wechat=customer.wechat,
        company_name=customer.company_name,
        industry=customer.industry,
        source_channel=customer.source_channel,
        customer_status=customer.customer_status,
        owner_user_id=customer.owner_user_id,
        owner_name=owner.name if owner else None,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
        last_followup_at=customer.last_followup_at,
        tags=[{"id": t.id, "tag_name": t.tag_name, "tag_type": t.tag_type} for t in tags],
    )
