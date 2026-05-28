"""
Role-based access control helpers.

These decorators enforce permissions on the SERVER side: they check the
logged-in user's `role` before letting a view run. This means access is
controlled by the backend, not just by hiding buttons in templates.

Usage:
    from accounts.permissions import role_required
    from accounts.models import User

    @role_required(User.Role.ADMIN, User.Role.ASSET_MANAGER)
    def some_view(request):
        ...
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*allowed_roles):
    """
    Allow the view only for logged-in users whose role is in allowed_roles.

    - Not logged in  -> redirected to the login page (via login_required).
    - Logged in but wrong role -> 403 Forbidden (PermissionDenied).
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return wrapper

    return decorator
