"""Test the EyeOnSaur device."""

import pytest

from custom_components.eyeonsaur.device import SaurDevice

pytestmark = pytest.mark.asyncio


async def test_saur_device_creation() -> None:
    """Test the creation of a SaurDevice."""
    unique_id = "123"
    manufacturer = "TestManuf"
    model = "TestModel"
    serial_number = "TestSN"
    created_at = "TestDate"

    device = SaurDevice(
        unique_id=unique_id,
        manufacturer=manufacturer,
        model=model,
        serial_number=serial_number,
        created_at=created_at,
    )

    assert device.unique_id == unique_id
    assert device.manufacturer == manufacturer
    assert device.model == model
    assert device.serial_number == serial_number
    assert device.created_at == created_at
