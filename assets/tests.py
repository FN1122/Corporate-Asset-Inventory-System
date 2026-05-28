"""Tests for asset features: depreciation math and inventory constraints."""

from datetime import date, timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase

from assets.depreciation import current_value
from assets.models import Asset, AssetCategory
from inventory.models import InventoryItem


class DepreciationTests(TestCase):
    def setUp(self):
        self.category = AssetCategory.objects.create(name="Laptops")

    def _make_asset(self, purchase_date, cost):
        return Asset.objects.create(
            name="X",
            category=self.category,
            purchase_date=purchase_date,
            purchase_cost=Decimal(cost),
            status=Asset.Status.AVAILABLE,
        )

    def test_brand_new_asset_is_worth_close_to_full_cost(self):
        asset = self._make_asset(date.today(), "1000.00")
        value = current_value(asset)
        self.assertAlmostEqual(float(value), 1000.0, delta=1.0)

    def test_value_after_useful_life_is_zero(self):
        ten_years_ago = date.today() - timedelta(days=365 * 10)
        asset = self._make_asset(ten_years_ago, "1000.00")
        self.assertEqual(current_value(asset), Decimal("0.00"))

    def test_midlife_value_is_roughly_half(self):
        two_and_a_half_years_ago = date.today() - timedelta(days=int(365.25 * 2.5))
        asset = self._make_asset(two_and_a_half_years_ago, "1000.00")
        value = float(current_value(asset))
        self.assertAlmostEqual(value, 500.0, delta=5.0)


class InventoryTests(TestCase):
    def test_cannot_save_negative_quantity(self):
        # PositiveIntegerField + DB CheckConstraint both prevent this.
        with self.assertRaises(Exception):
            with transaction.atomic():
                InventoryItem.objects.create(
                    item_name="bad", quantity_available=-1, reorder_level=0
                )

    def test_low_stock_detection(self):
        low = InventoryItem.objects.create(
            item_name="low", quantity_available=2, reorder_level=5
        )
        ok = InventoryItem.objects.create(
            item_name="ok", quantity_available=20, reorder_level=5
        )
        self.assertTrue(low.is_low_stock)
        self.assertFalse(ok.is_low_stock)
