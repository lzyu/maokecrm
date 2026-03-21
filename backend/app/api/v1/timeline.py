"""Timeline API endpoints - aggregates customer events."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_session
from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.permissions import can_access_all_customers
from app.models.customer import Customer

router = APIRouter()


class TimelineEvent(BaseModel):
    """Timeline event response schema."""

    id: int
    event_type: str
    event_type_label: str
    event_time: str
    title: str
    description: str | None
    operator_id: int | None
    operator_name: str | None
    reference_id: int | None
    extra_data: dict | None = None


class TimelineResponse(BaseModel):
    """Timeline response schema."""

    items: list[TimelineEvent]
    total: int
    customer_id: int
    customer_name: str


# Event type labels
EVENT_TYPE_LABELS = {
    "followup": "跟进记录",
    "service_record": "服务记录",
    "opportunity": "销售机会",
    "reminder": "提醒",
    "purchase": "购课记录",
    "attendance": "上课记录",
    "consultation": "咨询分析",
    "customer_created": "客户创建",
    "status_change": "状态变更",
}


@router.get("/{customer_id}", response_model=TimelineResponse)
async def get_customer_timeline(
    customer_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Get customer timeline - aggregates followups, service records, opportunities, reminders, etc.
    """
    # Verify customer exists and user has access
    customer_query = text("SELECT id, name, owner_user_id FROM customers WHERE id = :id AND deleted_at IS NULL")
    result = await session.execute(customer_query, {"id": customer_id})
    customer = result.fetchone()

    if not customer:
        raise NotFoundException("Customer not found")

    # Check permission
    if not can_access_all_customers(current_user.role_name):
        if customer[2] != current_user.id:
            raise ForbiddenException("You don't have access to this customer")

    offset = (page - 1) * page_size
    events = []

    # 1. Fetch followups
    followup_query = text("""
        SELECT sf.id, sf.followup_time, sf.contact_method, sf.content, sf.result,
               sf.sales_id, u.name as sales_name
        FROM sales_followups sf
        LEFT JOIN users u ON sf.sales_id = u.id
        WHERE sf.customer_id = :customer_id AND sf.deleted_at IS NULL
        ORDER BY sf.followup_time DESC
    """)
    result = await session.execute(followup_query, {"customer_id": customer_id})
    for row in result.fetchall():
        contact_method_labels = {
            "phone": "电话",
            "wechat": "微信",
            "visit": "拜访",
            "email": "邮件",
            "other": "其他",
        }
        result_labels = {
            "no_answer": "未接通",
            "contacted": "已联系",
            "interested": "有意向",
            "rejected": "已拒绝",
            "pending": "待跟进",
        }
        events.append(TimelineEvent(
            id=row[0],
            event_type="followup",
            event_type_label=EVENT_TYPE_LABELS["followup"],
            event_time=row[1].isoformat() if row[1] else "",
            title=f"{contact_method_labels.get(row[2], row[2])}跟进",
            description=row[3],
            operator_id=row[5],
            operator_name=row[6],
            reference_id=row[0],
            extra_data={"contact_method": row[2], "result": row[4], "result_label": result_labels.get(row[4])}
        ))

    # 2. Fetch service records
    service_query = text("""
        SELECT sr.id, sr.service_time, sr.service_content, sr.satisfaction_score,
               sr.consultant_id, u.name as consultant_name
        FROM service_records sr
        LEFT JOIN users u ON sr.consultant_id = u.id
        WHERE sr.customer_id = :customer_id AND sr.deleted_at IS NULL
        ORDER BY sr.service_time DESC
    """)
    result = await session.execute(service_query, {"customer_id": customer_id})
    for row in result.fetchall():
        events.append(TimelineEvent(
            id=row[0],
            event_type="service_record",
            event_type_label=EVENT_TYPE_LABELS["service_record"],
            event_time=row[1].isoformat() if row[1] else "",
            title="服务记录",
            description=row[2],
            operator_id=row[4],
            operator_name=row[5],
            reference_id=row[0],
            extra_data={"satisfaction_score": row[3]}
        ))

    # 3. Fetch sales opportunities
    opportunity_query = text("""
        SELECT so.id, so.created_at, so.stage, so.expected_amount, so.currency,
               so.owner_user_id, u.name as owner_name
        FROM sales_opportunities so
        LEFT JOIN users u ON so.owner_user_id = u.id
        WHERE so.customer_id = :customer_id AND so.deleted_at IS NULL
        ORDER BY so.created_at DESC
    """)
    result = await session.execute(opportunity_query, {"customer_id": customer_id})
    stage_labels = {
        "new": "新建",
        "qualified": "已验证",
        "proposal": "提案中",
        "negotiation": "谈判中",
        "won": "已成交",
        "lost": "已丢失",
    }
    for row in result.fetchall():
        events.append(TimelineEvent(
            id=row[0],
            event_type="opportunity",
            event_type_label=EVENT_TYPE_LABELS["opportunity"],
            event_time=row[1].isoformat() if row[1] else "",
            title=f"销售机会 - {stage_labels.get(row[2], row[2])}",
            description=f"预期金额: {row[3]} {row[4]}" if row[3] else None,
            operator_id=row[5],
            operator_name=row[6],
            reference_id=row[0],
            extra_data={"stage": row[2], "stage_label": stage_labels.get(row[2]), "expected_amount": float(row[3]) if row[3] else None, "currency": row[4]}
        ))

    # 4. Fetch reminders
    reminder_query = text("""
        SELECT sr.id, sr.reminder_time, sr.reminder_type, sr.content, sr.status, sr.priority,
               sr.assignee_user_id, u.name as assignee_name
        FROM service_reminders sr
        LEFT JOIN users u ON sr.assignee_user_id = u.id
        WHERE sr.customer_id = :customer_id AND sr.deleted_at IS NULL
        ORDER BY sr.reminder_time DESC
    """)
    result = await session.execute(reminder_query, {"customer_id": customer_id})
    reminder_type_labels = {
        "followup": "跟进提醒",
        "renewal": "续费提醒",
        "progress_check": "进度检查",
        "other": "其他",
    }
    for row in result.fetchall():
        events.append(TimelineEvent(
            id=row[0],
            event_type="reminder",
            event_type_label=EVENT_TYPE_LABELS["reminder"],
            event_time=row[1].isoformat() if row[1] else "",
            title=reminder_type_labels.get(row[2], row[2]),
            description=row[3],
            operator_id=row[6],
            operator_name=row[7],
            reference_id=row[0],
            extra_data={"reminder_type": row[2], "status": row[4], "priority": row[5]}
        ))

    # 5. Fetch course purchase records
    purchase_query = text("""
        SELECT cpr.id, cpr.purchase_date, cpr.course_name, cpr.amount, cpr.currency
        FROM course_purchase_records cpr
        WHERE cpr.customer_id = :customer_id AND cpr.deleted_at IS NULL
        ORDER BY cpr.purchase_date DESC
    """)
    result = await session.execute(purchase_query, {"customer_id": customer_id})
    for row in result.fetchall():
        events.append(TimelineEvent(
            id=row[0],
            event_type="purchase",
            event_type_label=EVENT_TYPE_LABELS["purchase"],
            event_time=row[1].isoformat() if row[1] else "",
            title=f"购课: {row[2]}",
            description=f"金额: {row[3]} {row[4]}" if row[3] else None,
            operator_id=None,
            operator_name=None,
            reference_id=row[0],
            extra_data={"course_name": row[2], "amount": float(row[3]) if row[3] else None, "currency": row[4]}
        ))

    # 6. Fetch course attendance records
    attendance_query = text("""
        SELECT car.id, car.class_date, car.course_name, car.status
        FROM course_attendance_records car
        WHERE car.customer_id = :customer_id AND car.deleted_at IS NULL
        ORDER BY car.class_date DESC
    """)
    result = await session.execute(attendance_query, {"customer_id": customer_id})
    attendance_status_labels = {
        "attended": "已上课",
        "absent": "缺课",
        "leave": "请假",
    }
    for row in result.fetchall():
        events.append(TimelineEvent(
            id=row[0],
            event_type="attendance",
            event_type_label=EVENT_TYPE_LABELS["attendance"],
            event_time=row[1].isoformat() if row[1] else "",
            title=f"上课: {row[2]}",
            description=f"状态: {attendance_status_labels.get(row[3], row[3])}",
            operator_id=None,
            operator_name=None,
            reference_id=row[0],
            extra_data={"course_name": row[2], "status": row[3], "status_label": attendance_status_labels.get(row[3])}
        ))

    # 7. Fetch consultation analysis
    consultation_query = text("""
        SELECT ca.id, ca.created_at, ca.analysis_summary, ca.consultant_id, u.name as consultant_name
        FROM consultation_analysis ca
        LEFT JOIN users u ON ca.consultant_id = u.id
        WHERE ca.customer_id = :customer_id AND ca.deleted_at IS NULL
        ORDER BY ca.created_at DESC
    """)
    result = await session.execute(consultation_query, {"customer_id": customer_id})
    for row in result.fetchall():
        events.append(TimelineEvent(
            id=row[0],
            event_type="consultation",
            event_type_label=EVENT_TYPE_LABELS["consultation"],
            event_time=row[1].isoformat() if row[1] else "",
            title="咨询分析",
            description=row[2],
            operator_id=row[3],
            operator_name=row[4],
            reference_id=row[0],
            extra_data=None
        ))

    # 8. Add customer creation event
    customer_created_query = text("""
        SELECT c.created_at, c.created_by, u.name as creator_name
        FROM customers c
        LEFT JOIN users u ON c.created_by = u.id
        WHERE c.id = :id
    """)
    result = await session.execute(customer_created_query, {"id": customer_id})
    row = result.fetchone()
    if row and row[0]:
        events.append(TimelineEvent(
            id=0,
            event_type="customer_created",
            event_type_label=EVENT_TYPE_LABELS["customer_created"],
            event_time=row[0].isoformat() if row[0] else "",
            title="客户创建",
            description="客户信息首次录入系统",
            operator_id=row[1],
            operator_name=row[2],
            reference_id=customer_id,
            extra_data=None
        ))

    # Sort all events by time descending
    events.sort(key=lambda x: x.event_time, reverse=True)

    # Paginate
    total = len(events)
    paginated_events = events[offset:offset + page_size]

    return TimelineResponse(
        items=paginated_events,
        total=total,
        customer_id=customer_id,
        customer_name=customer[1],
    )
