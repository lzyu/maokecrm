# SQLModel ORM models
# Import all models to ensure relationships are resolved correctly

from app.models.user import Role, User
from app.models.customer import Customer, CustomerTag, Tag
from app.models.sales import SalesFollowup, SalesOpportunity
from app.models.service import ServiceRecord, ServiceReminder
from app.models.import_model import ImportBatch, ImportError, CoursePurchaseRecord, CourseAttendanceRecord
from app.models.audit import AuditLog, ConsultationAnalysis
from app.models.timeline import PipelineEvent

__all__ = [
    "Role", "User",
    "Customer", "CustomerTag", "Tag",
    "SalesFollowup", "SalesOpportunity",
    "ServiceRecord", "ServiceReminder",
    "ImportBatch", "ImportError", "CoursePurchaseRecord", "CourseAttendanceRecord",
    "AuditLog", "ConsultationAnalysis",
    "PipelineEvent",
]
