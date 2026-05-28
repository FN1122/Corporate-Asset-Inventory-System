"""
Scheduled background tasks for CAIMS.

These run via Celery (triggered by Celery Beat on a schedule), NOT during
web requests. The two required jobs:

1. daily_low_stock_report  - find inventory items at/below reorder level
                             and email a summary to managers.
2. unreturned_asset_reminders - find assets that are overdue for return
                             and email reminders.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone


@shared_task
def daily_low_stock_report():
    """Email a report of all inventory items that are low on stock."""
    from inventory.models import InventoryItem

    low_items = [i for i in InventoryItem.objects.all() if i.is_low_stock]

    if not low_items:
        return "No low-stock items today."

    lines = [
        f"- {i.item_name}: {i.quantity_available} left (reorder at {i.reorder_level})"
        for i in low_items
    ]
    body = "The following items are at or below their reorder level:\n\n" + "\n".join(lines)

    send_mail(
        subject="CAIMS Daily Low-Stock Report",
        message=body,
        from_email="caims@example.com",
        recipient_list=["managers@example.com"],
        fail_silently=False,
    )
    return f"Low-stock report sent for {len(low_items)} item(s)."


@shared_task
def unreturned_asset_reminders():
    """Email reminders for assignments that are overdue (past due_date)."""
    from requests_app.models import AssetAssignment

    today = timezone.now().date()
    overdue = AssetAssignment.objects.filter(
        return_date__isnull=True,
        due_date__lt=today,
    ).select_related("asset", "employee")

    sent = 0
    for assignment in overdue:
        send_mail(
            subject="CAIMS: Asset return overdue",
            message=(
                f"Hi {assignment.employee.username},\n\n"
                f"The asset '{assignment.asset.name}' was due back on "
                f"{assignment.due_date}. Please return it as soon as possible.\n\n"
                f"Thank you,\nCAIMS"
            ),
            from_email="caims@example.com",
            recipient_list=[assignment.employee.email or "employee@example.com"],
            fail_silently=False,
        )
        sent += 1

    return f"Sent {sent} overdue reminder(s)."
