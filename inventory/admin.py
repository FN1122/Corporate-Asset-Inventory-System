from django.contrib import admin

from .models import InventoryItem


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("item_name", "quantity_available", "reorder_level", "is_low_stock", "updated_at")
    search_fields = ("item_name",)

    @admin.display(boolean=True, description="Low stock?")
    def is_low_stock(self, obj):
        return obj.is_low_stock
