"""
Business logic for the request / approval / assignment / return workflow.

Keeping this logic here (rather than in views) means the rules are in one
place and can be tested directly. All state-changing operations run inside
a database transaction so the system never ends up half-updated.
"""

from django.db import transaction
from django.utils import timezone

from assets.models import Asset
from audit.models import AuditLog

from .models import AssetAssignment, AssetRequest


class WorkflowError(Exception):
    """Raised when a workflow rule is violated (shown to the user)."""


@transaction.atomic
def approve_request(asset_request, reviewer):
    """
    Approve a pending request: create an assignment and mark the asset
    Assigned. Enforces the core business rules.
    """
    if asset_request.status != AssetRequest.Status.PENDING:
        raise WorkflowError("This request has already been reviewed.")

    # Rule: a user cannot approve their own request.
    if asset_request.employee_id == reviewer.id:
        raise WorkflowError("You cannot approve your own request.")

    # Lock the asset row to avoid a race with another simultaneous approval.
    asset = Asset.objects.select_for_update().get(pk=asset_request.asset_id)

    # Rule: the asset must still be available.
    if asset.status != Asset.Status.AVAILABLE:
        raise WorkflowError(f"'{asset.name}' is no longer available.")

    # Create the assignment (the DB also guards against double active-assignment).
    AssetAssignment.objects.create(asset=asset, employee=asset_request.employee)

    asset.status = Asset.Status.ASSIGNED
    asset.save(update_fields=["status"])

    asset_request.status = AssetRequest.Status.APPROVED
    asset_request.reviewed_by = reviewer
    asset_request.reviewed_date = timezone.now()
    asset_request.save(update_fields=["status", "reviewed_by", "reviewed_date"])

    AuditLog.objects.create(
        user=reviewer,
        action="Request approved",
        detail=f"{reviewer.username} approved {asset_request.employee.username}'s "
               f"request for '{asset.name}'.",
    )
    return asset_request


@transaction.atomic
def reject_request(asset_request, reviewer):
    """Reject a pending request. Nothing else changes."""
    if asset_request.status != AssetRequest.Status.PENDING:
        raise WorkflowError("This request has already been reviewed.")

    if asset_request.employee_id == reviewer.id:
        raise WorkflowError("You cannot reject your own request.")

    asset_request.status = AssetRequest.Status.REJECTED
    asset_request.reviewed_by = reviewer
    asset_request.reviewed_date = timezone.now()
    asset_request.save(update_fields=["status", "reviewed_by", "reviewed_date"])

    AuditLog.objects.create(
        user=reviewer,
        action="Request rejected",
        detail=f"{reviewer.username} rejected {asset_request.employee.username}'s "
               f"request for '{asset_request.asset.name}'.",
    )
    return asset_request


@transaction.atomic
def return_asset(assignment, actor):
    """
    Mark an active assignment as returned and set the asset back to Available.
    """
    if not assignment.is_active:
        raise WorkflowError("This asset has already been returned.")

    asset = Asset.objects.select_for_update().get(pk=assignment.asset_id)

    assignment.return_date = timezone.now()
    assignment.save(update_fields=["return_date"])

    asset.status = Asset.Status.AVAILABLE
    asset.save(update_fields=["status"])

    AuditLog.objects.create(
        user=actor,
        action="Asset returned",
        detail=f"'{asset.name}' returned by {assignment.employee.username}.",
    )
    return assignment
