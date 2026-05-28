from django.conf import settings
from django.db import models


class AssetCategory(models.Model):
    """A grouping for assets, e.g. 'Laptops', 'Vehicles', 'Furniture'."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Asset categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Asset(models.Model):
    """A trackable physical asset (a specific laptop, vehicle, etc.)."""

    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        ASSIGNED = "ASSIGNED", "Assigned"
        MAINTENANCE = "MAINTENANCE", "Maintenance"
        SCRAPPED = "SCRAPPED", "Scrapped"

    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        AssetCategory,
        on_delete=models.PROTECT,   # can't delete a category that still has assets
        related_name="assets",
    )
    purchase_date = models.DateField()
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    current_location = models.CharField(max_length=200, blank=True)
    qr_code = models.ImageField(upload_to="qr_codes/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return f"{self.name} [{self.get_status_display()}]"


class DepreciationRecord(models.Model):
    """A snapshot of an asset's calculated value at a point in time."""

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,   # delete records if the asset is deleted
        related_name="depreciation_records",
    )
    value = models.DecimalField(max_digits=12, decimal_places=2)
    date_recorded = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-date_recorded"]

    def __str__(self):
        return f"{self.asset.name}: {self.value} on {self.date_recorded}"
