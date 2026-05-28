from django.contrib import admin

from .models import AssetAssignment, AssetRequest


@admin.register(AssetRequest)
class AssetRequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "asset", "status", "request_date", "reviewed_by", "reviewed_date")
    list_filter = ("status", "request_date")
    search_fields = ("employee__username", "asset__name")
    date_hierarchy = "request_date"


@admin.register(AssetAssignment)
class AssetAssignmentAdmin(admin.ModelAdmin):
    list_display = ("asset", "employee", "assigned_date", "due_date", "return_date", "is_active")
    list_filter = ("assigned_date", "return_date")
    search_fields = ("asset__name", "employee__username")
    date_hierarchy = "assigned_date"

    @admin.display(boolean=True, description="Active?")
    def is_active(self, obj):
        return obj.is_active
