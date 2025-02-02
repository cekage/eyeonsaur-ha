"""Test the SaurCoordinator."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eyeonsaur.coordinator import SaurCoordinator
from custom_components.eyeonsaur.helpers.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    DOMAIN,
    ENTRY_CREATED_AT,
    ENTRY_MANUFACTURER,
    ENTRY_MODEL,
    ENTRY_SERIAL_NUMBER,
)
from custom_components.eyeonsaur.helpers.saur_db import SaurDatabaseError

pytestmark = pytest.mark.asyncio


@pytest.fixture(name="mock_config_entry")
def mock_config_entry_fixture() -> MockConfigEntry:
    """Mock the config_entry fixture."""
    return MockConfigEntry(
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


@pytest.fixture(name="mock_saur_client")
def mock_saur_client_fixture() -> MagicMock:
    """Mock the SaurClient."""
    client = MagicMock()
    client.authenticate = AsyncMock(return_value="fake_token")
    client.get_deliverypoints_data = AsyncMock(
        return_value={
            "meter": {
                "meterBrandCode": "TestManuf",
                "meterModelCode": "TestModel",
                "trueRegistrationNumber": "TestSN",
                "installationDate": "2023-01-01",
            }
        }
    )
    client.default_section_id = "123"
    client.get_lastknown_data = AsyncMock(
        side_effect=[
            None,  # Première fois : valeur vide pour first_refresh
            {
                "readingDate": "2024-01-15",
                "indexValue": 123,
            },  # Deuxième fois : valeur pour update_data_success
            {
                "readingDate": "2025-01-01T00:00:00",
                "indexValue": 123,
            },  # Troisième fois : valeur pour missing dates
        ]
    )
    client.get_monthly_data = AsyncMock(
        return_value={
            "consumptions": [
                {
                    "rangeType": "Day",
                    "startDate": "2024-01-10 00:00:00",
                    "value": 1.234,
                }
            ]
        }
    )
    return client


async def test_coordinator_init(hass: HomeAssistant, mock_config_entry):
    """Test SaurCoordinator initialization."""
    db_helper = AsyncMock()
    recorder = AsyncMock()
    coordinator = SaurCoordinator(hass, mock_config_entry, db_helper, recorder)

    assert coordinator.client is not None
    assert coordinator.db_helper is db_helper
    assert coordinator.recorder is recorder
    assert coordinator.data is None


async def test_async_config_entry_first_refresh_success(
    hass: HomeAssistant,
    mock_config_entry,
    mock_saur_client,
):
    """Test successful first refresh."""
    db_helper = AsyncMock()
    recorder = AsyncMock()
    coordinator = SaurCoordinator(hass, mock_config_entry, db_helper, recorder)
    coordinator.client = mock_saur_client

    # Mock data for deliverypoints
    mock_saur_client.get_deliverypoints_data.return_value = {
        "meter": {
            "installationDate": "2023-01-01",
            "meterBrandCode": "TestManuf",
            "meterModelCode": "TestModel",
            "trueRegistrationNumber": "TestSN",
        }
    }

    await coordinator.async_config_entry_first_refresh()

    db_helper.async_init_db.assert_awaited_once()
    mock_saur_client.authenticate.assert_awaited_once()
    mock_saur_client.get_deliverypoints_data.assert_awaited_once()

    assert coordinator.base_data is not None
    assert coordinator.base_data["releve_physique"]["date"] is None
    assert coordinator.base_data["releve_physique"]["valeur"] is None
    assert coordinator.base_data["created_at"] == "2023-01-01"
    assert (
        coordinator.base_data["section_id"]
        == mock_saur_client.default_section_id
    )
    assert coordinator.base_data["manufacturer"] == "TestManuf"
    assert coordinator.base_data["model"] == "TestModel"
    assert coordinator.base_data["serial_number"] == "TestSN"


async def test_async_config_entry_first_refresh_db_failure(
    hass: HomeAssistant, mock_config_entry, mock_saur_client
):
    """Test first refresh with database initialization failure."""
    db_helper = AsyncMock()
    recorder = AsyncMock()
    coordinator = SaurCoordinator(hass, mock_config_entry, db_helper, recorder)
    coordinator.client = mock_saur_client
    db_helper.async_init_db.side_effect = SaurDatabaseError("Database error")

    with pytest.raises(UpdateFailed) as excinfo:
        await coordinator.async_config_entry_first_refresh()

    assert "Error initializing database" in str(excinfo.value)
