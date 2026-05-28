from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    An append-only record of significant actions in the system
    (asset created, assigned, returned, status changed, etc.).

    Entries are meant to be written once and never edited or deleted —
    that immutability is what makes it a trustworthy audit trail.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,   # keep the log even if the user is removed
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=255)
    detail = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [models.Index(fields=["timestamp"])]

    def __str__(self):
        who = self.user.username if self.user else "system"
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {who}: {self.action}"
