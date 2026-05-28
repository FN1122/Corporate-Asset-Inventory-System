from django.db import models


class InventoryItem(models.Model):
    """A consumable stock item, e.g. 'HDMI cables', 'Printer paper'."""

    item_name = models.CharField(max_length=200, unique=True)
    quantity_available = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(
        default=0,
        help_text="When quantity falls to or below this number, the item is low on stock.",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["item_name"]
        constraints = [
            # Database-level guard: stock can never go negative.
            models.CheckConstraint(
                condition=models.Q(quantity_available__gte=0),
                name="inventory_quantity_non_negative",
            ),
        ]

    @property
    def is_low_stock(self):
        return self.quantity_available <= self.reorder_level

    def __str__(self):
        return f"{self.item_name} ({self.quantity_available} in stock)"
