from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Admin configuration for the custom User model.

    Extends Django's built-in UserAdmin so we keep all the standard user
    management (password handling, permissions, etc.) and add our `role`
    field to the list view and the edit/add forms.
    """

    # Columns shown in the user list page
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email")

    # Add the "Role" section to the user EDIT form.
    # (UserAdmin.fieldsets is the default set; we append our own section.)
    fieldsets = UserAdmin.fieldsets + (
        ("Role", {"fields": ("role",)}),
    )

    # Add the role field to the user ADD form (the screen shown when
    # creating a brand-new user from the admin).
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Role", {"fields": ("role",)}),
    )
