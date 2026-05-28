from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from accounts.permissions import role_required

from .forms import AssetForm
from .models import Asset, AssetCategory
from .qr import generate_qr_code

# Roles allowed to create/edit assets.
MANAGE_ROLES = (User.Role.ADMIN, User.Role.ASSET_MANAGER)


@login_required
def asset_list(request):
    """List all assets. Viewable by any logged-in user."""
    assets = Asset.objects.select_related("category").all()

    # Optional filtering by status / category via query params.
    status = request.GET.get("status")
    category = request.GET.get("category")
    if status:
        assets = assets.filter(status=status)
    if category:
        assets = assets.filter(category_id=category)

    context = {
        "assets": assets,
        "statuses": Asset.Status.choices,
        "categories": AssetCategory.objects.all(),
        "selected_status": status,
        "selected_category": category,
        "can_manage": request.user.role in MANAGE_ROLES,
    }
    return render(request, "assets/asset_list.html", context)


@login_required
def asset_detail(request, pk):
    """Show one asset, its QR code, and depreciation history."""
    asset = get_object_or_404(
        Asset.objects.select_related("category"), pk=pk
    )
    context = {
        "asset": asset,
        "depreciation_records": asset.depreciation_records.all(),
        "can_manage": request.user.role in MANAGE_ROLES,
    }
    return render(request, "assets/asset_detail.html", context)


@role_required(*MANAGE_ROLES)
def asset_create(request):
    """Create a new asset and generate its QR code."""
    if request.method == "POST":
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save()              # save once to get an id
            generate_qr_code(asset)          # build QR using that id
            asset.save()                     # save again to store the image
            return redirect("asset_detail", pk=asset.pk)
    else:
        form = AssetForm()

    return render(request, "assets/asset_form.html", {"form": form, "mode": "Add"})


@role_required(*MANAGE_ROLES)
def asset_edit(request, pk):
    """Edit an existing asset."""
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == "POST":
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            asset = form.save()
            # Regenerate QR if it doesn't have one yet.
            if not asset.qr_code:
                generate_qr_code(asset)
                asset.save()
            return redirect("asset_detail", pk=asset.pk)
    else:
        form = AssetForm(instance=asset)

    return render(
        request, "assets/asset_form.html", {"form": form, "mode": "Edit", "asset": asset}
    )
