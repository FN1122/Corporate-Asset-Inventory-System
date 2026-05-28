"""Helper for generating QR codes for assets."""

from io import BytesIO

import qrcode
from django.core.files.base import ContentFile


def generate_qr_code(asset):
    """
    Generate a QR code image for the given asset and save it to the
    asset's `qr_code` field.

    The QR encodes a small text payload identifying the asset. Scanning it
    (with any phone) shows the asset id and name — enough to look it up.
    """
    payload = f"CAIMS-ASSET|id={asset.id}|name={asset.name}"

    qr = qrcode.make(payload)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    filename = f"asset_{asset.id}.png"
    # save=False here; the caller saves the asset once, avoiding a double write.
    asset.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
