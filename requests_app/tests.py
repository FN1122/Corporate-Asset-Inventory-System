"""
Tests for the request/approval/assignment workflow.

These cover the core business rules from the implementation plan:
- A user cannot approve their own request.
- An asset cannot be assigned twice at the same time.
- A pending request can only be approved if the asset is still available.
- Approval atomically creates the assignment and flips the asset's status.
- Returning an asset releases it back to Available.
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import User
from assets.models import Asset, AssetCategory
from requests_app.models import AssetAssignment, AssetRequest
from requests_app.services import (
    WorkflowError,
    approve_request,
    reject_request,
    return_asset,
)

UserModel = get_user_model()


class WorkflowTests(TestCase):
    def setUp(self):
        self.employee = UserModel.objects.create_user(
            username="alice", password="x", role=User.Role.EMPLOYEE,
        )
        self.manager = UserModel.objects.create_user(
            username="bob", password="x", role=User.Role.ASSET_MANAGER,
        )
        self.category = AssetCategory.objects.create(name="Laptops")
        self.asset = Asset.objects.create(
            name="Test Laptop",
            category=self.category,
            purchase_date=date(2024, 1, 1),
            purchase_cost=Decimal("1000.00"),
            status=Asset.Status.AVAILABLE,
        )

    def _make_request(self, employee=None, asset=None):
        return AssetRequest.objects.create(
            employee=employee or self.employee,
            asset=asset or self.asset,
        )

    # --- Rule: can't approve your own request ---
    def test_cannot_approve_own_request(self):
        req = self._make_request(employee=self.manager)
        with self.assertRaises(WorkflowError):
            approve_request(req, self.manager)
        req.refresh_from_db()
        self.assertEqual(req.status, AssetRequest.Status.PENDING)

    # --- Rule: approval flips asset to Assigned and creates an assignment ---
    def test_approve_creates_assignment_and_marks_asset_assigned(self):
        req = self._make_request()
        approve_request(req, self.manager)

        self.asset.refresh_from_db()
        req.refresh_from_db()

        self.assertEqual(self.asset.status, Asset.Status.ASSIGNED)
        self.assertEqual(req.status, AssetRequest.Status.APPROVED)
        self.assertTrue(
            AssetAssignment.objects.filter(
                asset=self.asset, employee=self.employee, return_date__isnull=True
            ).exists()
        )

    # --- Rule: asset must be available at approval time ---
    def test_cannot_approve_when_asset_not_available(self):
        self.asset.status = Asset.Status.MAINTENANCE
        self.asset.save()
        req = self._make_request()

        with self.assertRaises(WorkflowError):
            approve_request(req, self.manager)

    # --- Rule: DB blocks two simultaneous active assignments of one asset ---
    def test_db_prevents_two_active_assignments(self):
        AssetAssignment.objects.create(asset=self.asset, employee=self.employee)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AssetAssignment.objects.create(
                    asset=self.asset, employee=self.manager
                )

    # --- Return flow ---
    def test_return_sets_asset_back_to_available(self):
        req = self._make_request()
        approve_request(req, self.manager)
        assignment = AssetAssignment.objects.get(
            asset=self.asset, return_date__isnull=True
        )

        return_asset(assignment, self.employee)

        self.asset.refresh_from_db()
        assignment.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.AVAILABLE)
        self.assertIsNotNone(assignment.return_date)

    # --- Reject doesn't change the asset ---
    def test_reject_does_not_assign_asset(self):
        req = self._make_request()
        reject_request(req, self.manager)

        self.asset.refresh_from_db()
        req.refresh_from_db()
        self.assertEqual(req.status, AssetRequest.Status.REJECTED)
        self.assertEqual(self.asset.status, Asset.Status.AVAILABLE)
