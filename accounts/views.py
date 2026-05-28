from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard(request):
    """
    Landing page after login. Shows a role-aware welcome and a summary
    of what the current user can do. The actual feature pages get linked
    here as we build them in later phases.
    """
    context = {
        "role_label": request.user.get_role_display(),
    }
    return render(request, "dashboard.html", context)
