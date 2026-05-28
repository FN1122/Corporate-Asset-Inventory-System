from django.conf import settings
from django.db import models

from assets.models import Asset


class AssetRequest(models.Model):
    """An employee's request to be assigned a particular asset."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="asset_requests",
    )
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="requests",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    request_date = models.DateTimeField(auto_now_add=True)
    # Who actioned it (manager) and when — useful for the audit trail.
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_requests",
    )
    reviewed_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-request_date"]
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return f"{self.employee} -> {self.asset} ({self.get_status_display()})"


class AssetAssignment(models.Model):
    """A record of an asset being assigned to a user, and later returned."""

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    assigned_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Optional expected return date; used for overdue reminders.",
    )
    return_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-assigned_date"]
        constraints = [
            # An asset can only have ONE active (un-returned) assignment at a time.
            # A NULL return_date means "currently assigned".
            models.UniqueConstraint(
                fields=["asset"],
                condition=models.Q(return_date__isnull=True),
                name="one_active_assignment_per_asset",
            ),
        ]

    @property
    def is_active(self):
        return self.return_date is None

    def __str__(self):
        state = "active" if self.is_active else "returned"
        return f"{self.asset} -> {self.employee} ({state})"
