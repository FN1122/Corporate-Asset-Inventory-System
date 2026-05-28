from django import forms

from .models import Asset


class AssetForm(forms.ModelForm):
    """Form for creating and editing assets."""

    class Meta:
        model = Asset
        fields = [
            "name",
            "category",
            "purchase_date",
            "purchase_cost",
            "status",
            "current_location",
        ]
        widgets = {
            "purchase_date": forms.DateInput(attrs={"type": "date"}),
        }
