"""Tags API endpoints."""

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_session
from app.core.exceptions import ConflictException, NotFoundException
from app.core.permissions import is_admin_or_above
from app.models.customer import CustomerTag, Tag, TagRead

router = APIRouter()


class TagListResponse(BaseModel):
    items: list[TagRead]
    total: int


class TagCreateRequest(BaseModel):
    tag_name: str
    tag_type: str


class TagUpdateRequest(BaseModel):
    tag_name: str | None = None
    tag_type: str | None = None


@router.get("", response_model=TagListResponse)
async def list_tags(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    keyword: str | None = Query(None),
    tag_type: str | None = Query(None),
):
    """
    List all tags.
    """
    stmt = select(Tag)

    if keyword:
        stmt = stmt.where(Tag.tag_name.ilike(f"%{keyword}%"))

    if tag_type:
        stmt = stmt.where(Tag.tag_type == tag_type)

    stmt = stmt.order_by(Tag.created_at.desc())

    result = await session.execute(stmt)
    tags = result.scalars().all()

    return TagListResponse(
        items=[TagRead.model_validate(tag) for tag in tags],
        total=len(tags),
    )


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def create_tag(
    request: TagCreateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new tag.
    """
    # Check if tag exists
    existing_stmt = select(Tag).where(
        Tag.tag_name == request.tag_name,
        Tag.tag_type == request.tag_type
    )
    existing_result = await session.execute(existing_stmt)
    if existing_result.scalar_one_or_none():
        raise ConflictException("Tag with this name and type already exists")

    tag = Tag(
        tag_name=request.tag_name,
        tag_type=request.tag_type,
    )

    session.add(tag)
    await session.commit()
    await session.refresh(tag)

    return TagRead.model_validate(tag)


@router.put("/{tag_id}", response_model=TagRead)
async def update_tag(
    tag_id: int,
    request: TagUpdateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """
    Update tag by ID.
    """
    stmt = select(Tag).where(Tag.id == tag_id)
    result = await session.execute(stmt)
    tag = result.scalar_one_or_none()

    if not tag:
        raise NotFoundException("Tag not found")

    # Check uniqueness if changing
    if request.tag_name or request.tag_type:
        new_name = request.tag_name or tag.tag_name
        new_type = request.tag_type or tag.tag_type

        existing_stmt = select(Tag).where(
            Tag.tag_name == new_name,
            Tag.tag_type == new_type,
            Tag.id != tag_id
        )
        existing_result = await session.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            raise ConflictException("Tag with this name and type already exists")

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tag, field, value)

    session.add(tag)
    await session.commit()
    await session.refresh(tag)

    return TagRead.model_validate(tag)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete tag by ID.
    """
    if not is_admin_or_above(current_user.role_name):
        from app.core.exceptions import ForbiddenException
        raise ForbiddenException("Admin access required")

    stmt = select(Tag).where(Tag.id == tag_id)
    result = await session.execute(stmt)
    tag = result.scalar_one_or_none()

    if not tag:
        raise NotFoundException("Tag not found")

    # Delete customer-tag associations first
    delete_stmt = select(CustomerTag).where(CustomerTag.tag_id == tag_id)
    links_result = await session.execute(delete_stmt)
    for link in links_result.scalars().all():
        await session.delete(link)

    # Delete tag
    await session.delete(tag)
    await session.commit()
