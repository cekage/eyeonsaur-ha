"""Test the EyeOnSaur sensor."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, UnitOfVolume
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eyeonsaur.coordinator import SaurCoordinator
from custom_components.eyeonsaur.helpers.const import (
    DOMAIN,
    ENTRY_CREATED_AT,
    ENTRY_MANUFACTURER,
    ENTRY_MODEL,
    ENTRY_SERIAL_NUMBER,
)
from custom_components.eyeonsaur.helpers.saur_db import SaurDatabaseHelper
from custom_components.eyeonsaur.sensor import SaurSensor, async_setup_entry

pytestmark = pytest.mark.asyncio


async def test_async_setup_entry_adds_sensor(hass: HomeAssistant) -> None:
    """Test that async_setup_entry adds the sensor."""

    # Mock Config Entry
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "password",
            ENTRY_MANUFACTURER: "TestManuf",
            ENTRY_MODEL: "TestModel",
            ENTRY_SERIAL_NUMBER: "TestSN",
            ENTRY_CREATED_AT: "2023-01-15",
        },
    )
    config_entry.add_to_hass(hass)

    # Mock the async_add_entities function
    async_add_entities = AsyncMock()

    # Mock the SaurClient
    mock_client = AsyncMock()
    mock_client.authenticate = AsyncMock(return_value="fake_token")
    mock_client.get_deliverypoints_data = AsyncMock(
        return_value={
            "meter": {
                "meterBrandCode": "TestManuf",
                "meterModelCode": "TestModel",
                "trueRegistrationNumber": "TestSN",
                "installationDate": "2023-01-15",
            }
        }
    )
    mock_client.default_section_id = "123"
    mock_client.get_lastknown_data = AsyncMock(
        return_value={"readingDate": "2025-01-01T00:00:00", "indexValue": 123}
    )
    mock_client.get_monthly_data = AsyncMock(return_value={"consumptions": []})

    # Mock SaurDatabaseHelper
    mock_db_helper = MagicMock(spec=SaurDatabaseHelper)
    mock_db_helper.async_init_db = AsyncMock(return_value=None)
    mock_db_helper.async_update_anchor = AsyncMock(return_value=None)
    mock_db_helper.async_write_consumptions = AsyncMock(return_value=None)
    mock_db_helper.async_get_all_consumptions_with_absolute = AsyncMock(
        return_value=[]
    )

    # Mock recorder
    mock_recorder = MagicMock()

    # Create a mock coordinator
    coordinator = SaurCoordinator(
        hass, config_entry, mock_db_helper, mock_recorder
    )
    coordinator.client = mock_client
    coordinator.update_interval = None  # On empêche le timer d'être lancé

    async def first_refresh():
        await coordinator._async_update_data()
        raise Exception("Stop here")

    coordinator.async_config_entry_first_refresh = AsyncMock(
        side_effect=first_refresh
    )

    # Set up the config entry
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        "coordinator": coordinator
    }

    # Initialize coordinator data before calling async_setup_entry
    coordinator.data = {
        "releve_physique": {"date": None, "valeur": None},
        "created_at": "2023-01-15",
    }

    # Call async_setup_entry
    await async_setup_entry(hass, config_entry, async_add_entities)
    await hass.async_block_till_done()

    # Check that the sensor was added
    assert async_add_entities.call_count == 1

    # Check that the added entity is a SaurSensor
    sensor = async_add_entities.call_args[0][0][0]
    assert isinstance(sensor, SaurSensor)

    # Test the attributes of the added sensor
    assert sensor.name == f"{mock_client.default_section_id}"
    assert sensor.unique_id == f"{mock_client.default_section_id}_water"
    assert sensor._attr_device_class == SensorDeviceClass.WATER
    assert sensor._attr_native_unit_of_measurement == UnitOfVolume.CUBIC_METERS
    assert sensor._attr_state_class == SensorStateClass.TOTAL_INCREASING
    assert sensor.native_value is None
    assert sensor._attr_has_entity_name is True
    assert sensor._attr_translation_key == "water_consumption"

    # Test extra_state_attributes with data
    coordinator.data = {
        "releve_physique": {"date": "2023-01-15", "valeur": 100},
        "created_at": "2023-01-15",
    }
    expected_extra_attributes = {
        "state_class": "total_increasing",
        "physical_meter_date": "2023-01-15",
        "releve_physique_volume": 100,
        "installation_date": "2023-01-15",
    }
    assert sensor.extra_state_attributes == expected_extra_attributes

    # Test extra_state_attributes with empty data
    coordinator.data = {}
    expected_extra_attributes_empty = {
        "state_class": "total_increasing",
        "physical_meter_date": None,
        "releve_physique_volume": None,
        "installation_date": None,
    }
    assert sensor.extra_state_attributes == expected_extra_attributes_empty

    # Test that async_added_to_hass is called and updates state
    assert sensor._attr_suggested_display_precision == 0
    await sensor.async_added_to_hass()

    # Test device_info
    expected_device_info = {
        "identifiers": {(DOMAIN, "123")},
        "name": "Compteur SAUR",
        "manufacturer": "TestManuf",
        "model": "TestModel",
        "serial_number": "TestSN",
        "created_at": "2023-01-15",
        "entry_type": "service",
    }
    assert sensor.device_info == expected_device_info

    await coordinator.async_shutdown()
