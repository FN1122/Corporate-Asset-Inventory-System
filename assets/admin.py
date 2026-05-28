from django.contrib import admin

from .models import Asset, AssetCategory, DepreciationRecord


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


class DepreciationRecordInline(admin.TabularInline):
    """Show an asset's depreciation history right on the asset edit page."""
    model = DepreciationRecord
    extra = 0
    readonly_fields = ("value", "date_recorded")
    can_delete = False


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "status", "purchase_date", "purchase_cost", "current_location")
    list_filter = ("status", "category")
    search_fields = ("name",)
    date_hierarchy = "purchase_date"
    inlines = [DepreciationRecordInline]


@admin.register(DepreciationRecord)
class DepreciationRecordAdmin(admin.ModelAdmin):
    list_display = ("asset", "value", "date_recorded")
    list_filter = ("date_recorded",)
    search_fields = ("asset__name",)
