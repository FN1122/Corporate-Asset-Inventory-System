from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model for CAIMS.

    Extends Django's built-in AbstractUser (so we keep username, password
    hashing, authentication, and admin integration) and adds a `role` field
    that drives role-based access control across the system.
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        ASSET_MANAGER = "ASSET_MANAGER", "Asset Manager"
        EMPLOYEE = "EMPLOYEE", "Employee"
        AUDITOR = "AUDITOR", "Auditor"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        help_text="Determines what this user is allowed to do in the system.",
    )

    # Convenience helpers so views/templates can ask "is this user an X?"
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_asset_manager(self):
        return self.role == self.Role.ASSET_MANAGER

    @property
    def is_employee(self):
        return self.role == self.Role.EMPLOYEE

    @property
    def is_auditor(self):
        return self.role == self.Role.AUDITOR

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
