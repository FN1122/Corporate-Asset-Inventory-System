"""
Straight-line depreciation logic.

Straight-line is the simplest method: an asset loses an equal share of its
value each year over a fixed "useful life". After the useful life is up, the
asset is considered fully depreciated (value floored at 0).

    annual_depreciation = purchase_cost / useful_life_years
    current_value = purchase_cost - (annual_depreciation * years_elapsed)
"""

from datetime import date
from decimal import Decimal

# Default useful life in years, used for all assets.
DEFAULT_USEFUL_LIFE_YEARS = 5


def years_elapsed(purchase_date, as_of=None):
    """Whole + fractional years between purchase_date and as_of (default today)."""
    as_of = as_of or date.today()
    days = (as_of - purchase_date).days
    return max(days, 0) / 365.25


def current_value(asset, as_of=None, useful_life_years=DEFAULT_USEFUL_LIFE_YEARS):
    """
    Return the asset's depreciated value as of a given date (default today),
    floored at 0 and rounded to 2 decimal places.
    """
    cost = Decimal(asset.purchase_cost)
    elapsed = Decimal(str(years_elapsed(asset.purchase_date, as_of)))
    life = Decimal(useful_life_years)

    annual = cost / life
    depreciated = cost - (annual * elapsed)

    if depreciated < 0:
        depreciated = Decimal("0")

    return depreciated.quantize(Decimal("0.01"))


def record_depreciation(asset, as_of=None):
    """
    Calculate the current value and store it as a DepreciationRecord snapshot.
    Imported lazily to avoid a circular import with models.
    """
    from .models import DepreciationRecord

    value = current_value(asset, as_of=as_of)
    return DepreciationRecord.objects.create(asset=asset, value=value)
