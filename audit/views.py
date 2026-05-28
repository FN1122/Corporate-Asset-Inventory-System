from accounts.models import User
from accounts.permissions import role_required
from django.shortcuts import render

from .models import AuditLog

VIEW_ROLES = (User.Role.ADMIN, User.Role.AUDITOR)


@role_required(*VIEW_ROLES)
def audit_log_list(request):
    """
    Read-only view of the system audit trail. Available to Auditors and
    Admins. Supports a simple keyword search across the action/detail text.
    """
    logs = AuditLog.objects.select_related("user").all()

    q = request.GET.get("q", "").strip()
    if q:
        logs = logs.filter(action__icontains=q) | logs.filter(detail__icontains=q)
        logs = logs.distinct()

    return render(request, "audit/audit_list.html", {"logs": logs[:200], "q": q})
