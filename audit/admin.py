from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action")
    list_filter = ("timestamp",)
    search_fields = ("action", "detail", "user__username")
    date_hierarchy = "timestamp"

    # The audit log is append-only: no editing or deleting through the admin,
    # and all fields are read-only when viewing an entry.
    readonly_fields = ("user", "action", "detail", "timestamp")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
