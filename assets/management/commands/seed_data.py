"""
Management command to populate the database with a small set of demo data.

Run with:  python manage.py seed_data

Safe to run multiple times: it uses get_or_create, so re-running won't
create duplicate rows.
"""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from assets.models import Asset, AssetCategory
from inventory.models import InventoryItem
from requests_app.models import AssetAssignment

User = get_user_model()


class Command(BaseCommand):
    help = "Populate the database with a small set of demo data."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        # --- Categories ---
        laptops, _ = AssetCategory.objects.get_or_create(
            name="Laptops",
            defaults={"description": "Portable computers issued to staff."},
        )
        vehicles, _ = AssetCategory.objects.get_or_create(
            name="Vehicles",
            defaults={"description": "Company cars and vans."},
        )

        # --- Assets ---
        assets = [
            {
                "name": "Dell Latitude 5440",
                "category": laptops,
                "purchase_date": date(2024, 3, 15),
                "purchase_cost": "1200.00",
                "status": Asset.Status.AVAILABLE,
                "current_location": "IT Store Room",
            },
            {
                "name": "MacBook Pro 14",
                "category": laptops,
                "purchase_date": date(2023, 11, 1),
                "purchase_cost": "2400.00",
                "status": Asset.Status.ASSIGNED,
                "current_location": "Design Dept",
            },
            {
                "name": "Toyota Hilux",
                "category": vehicles,
                "purchase_date": date(2022, 6, 20),
                "purchase_cost": "35000.00",
                "status": Asset.Status.AVAILABLE,
                "current_location": "Main Depot",
            },
            {
                "name": "Ford Transit Van",
                "category": vehicles,
                "purchase_date": date(2021, 1, 10),
                "purchase_cost": "28000.00",
                "status": Asset.Status.MAINTENANCE,
                "current_location": "Service Garage",
            },
        ]
        for data in assets:
            Asset.objects.get_or_create(name=data["name"], defaults=data)

        # --- Inventory items (one deliberately below reorder level) ---
        items = [
            {"item_name": "HDMI Cables", "quantity_available": 50, "reorder_level": 10},
            {"item_name": "Printer Paper (reams)", "quantity_available": 8, "reorder_level": 15},  # low stock
            {"item_name": "USB-C Chargers", "quantity_available": 25, "reorder_level": 5},
        ]
        for data in items:
            InventoryItem.objects.get_or_create(
                item_name=data["item_name"], defaults=data
            )

        # --- Sample assignments ---
        # Ensure a demo employee exists to assign assets to.
        employee, created = User.objects.get_or_create(
            username="demo_employee",
            defaults={
                "email": "demo.employee@example.com",
                "role": getattr(User.Role, "EMPLOYEE", "EMPLOYEE"),
            },
        )
        if created:
            employee.set_password("demopass123")
            employee.save()

        # One ACTIVE assignment: the MacBook is currently out (no return date).
        macbook = Asset.objects.filter(name="MacBook Pro 14").first()
        if macbook:
            AssetAssignment.objects.get_or_create(
                asset=macbook,
                return_date__isnull=True,
                defaults={
                    "employee": employee,
                    "due_date": (timezone.now() + timedelta(days=30)).date(),
                },
            )
            macbook.status = Asset.Status.ASSIGNED
            macbook.save()

        # One RETURNED assignment: the Dell was assigned and given back.
        dell = Asset.objects.filter(name="Dell Latitude 5440").first()
        if dell and not dell.assignments.filter(return_date__isnull=False).exists():
            AssetAssignment.objects.create(
                asset=dell,
                employee=employee,
                return_date=timezone.now(),
            )

        self.stdout.write(self.style.SUCCESS("Done. Demo data created."))
