"""API v1 router that aggregates all route modules."""

from fastapi import APIRouter

from app.api.v1 import audit, auth, customers, followups, imports, opportunities, reminders, roles, services, tags, timeline, users

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(tags.router, prefix="/tags", tags=["Tags"])
api_router.include_router(followups.router, prefix="/followups", tags=["Followups"])
api_router.include_router(services.router, prefix="/services", tags=["Services"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["Reminders"])
api_router.include_router(imports.router, prefix="/imports", tags=["Imports"])
api_router.include_router(opportunities.router, prefix="/opportunities", tags=["Opportunities"])
api_router.include_router(timeline.router, prefix="/timeline", tags=["Timeline"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit"])
