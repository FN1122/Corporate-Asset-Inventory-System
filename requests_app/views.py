from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from accounts.permissions import role_required
from assets.models import Asset
from audit.models import AuditLog

from .models import AssetAssignment, AssetRequest
from .services import (
    WorkflowError,
    approve_request,
    reject_request,
    return_asset,
)

MANAGE_ROLES = (User.Role.ADMIN, User.Role.ASSET_MANAGER)


# ---------- Employee side ----------

@role_required(User.Role.EMPLOYEE)
def request_create(request):
    """Employee submits a request for an available asset."""
    available = Asset.objects.filter(status=Asset.Status.AVAILABLE)

    if request.method == "POST":
        asset_id = request.POST.get("asset")
        asset = get_object_or_404(Asset, pk=asset_id, status=Asset.Status.AVAILABLE)
        AssetRequest.objects.create(employee=request.user, asset=asset)
        AuditLog.objects.create(
            user=request.user,
            action="Request submitted",
            detail=f"{request.user.username} requested '{asset.name}'.",
        )
        messages.success(request, f"Request submitted for {asset.name}.")
        return redirect("my_requests")

    return render(request, "requests_app/request_create.html", {"available": available})


@role_required(User.Role.EMPLOYEE)
def my_requests(request):
    """Employee views their own requests and currently-held assets."""
    requests_qs = AssetRequest.objects.filter(
        employee=request.user
    ).select_related("asset")
    active_assignments = AssetAssignment.objects.filter(
        employee=request.user, return_date__isnull=True
    ).select_related("asset")
    return render(
        request,
        "requests_app/my_requests.html",
        {"requests": requests_qs, "active_assignments": active_assignments},
    )


@role_required(User.Role.EMPLOYEE)
def return_my_asset(request, pk):
    """Employee returns an asset assigned to them."""
    assignment = get_object_or_404(
        AssetAssignment, pk=pk, employee=request.user, return_date__isnull=True
    )
    if request.method == "POST":
        try:
            return_asset(assignment, request.user)
            messages.success(request, f"Returned {assignment.asset.name}.")
        except WorkflowError as e:
            messages.error(request, str(e))
        return redirect("my_requests")
    return redirect("my_requests")


# ---------- Manager side ----------

@role_required(*MANAGE_ROLES)
def approval_queue(request):
    """Managers see pending requests to approve or reject."""
    pending = AssetRequest.objects.filter(
        status=AssetRequest.Status.PENDING
    ).select_related("asset", "employee")
    return render(request, "requests_app/approval_queue.html", {"pending": pending})


@role_required(*MANAGE_ROLES)
def request_approve(request, pk):
    asset_request = get_object_or_404(AssetRequest, pk=pk)
    if request.method == "POST":
        try:
            approve_request(asset_request, request.user)
            messages.success(request, "Request approved and asset assigned.")
        except WorkflowError as e:
            messages.error(request, str(e))
    return redirect("approval_queue")


@role_required(*MANAGE_ROLES)
def request_reject(request, pk):
    asset_request = get_object_or_404(AssetRequest, pk=pk)
    if request.method == "POST":
        try:
            reject_request(asset_request, request.user)
            messages.success(request, "Request rejected.")
        except WorkflowError as e:
            messages.error(request, str(e))
    return redirect("approval_queue")
