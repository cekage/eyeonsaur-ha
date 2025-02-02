"""Test the EyeOnSaur config flow."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.eyeonsaur.coordinator import SaurCoordinator
from custom_components.eyeonsaur.helpers.const import (
    DOMAIN,
    ENTRY_LOGIN,
    ENTRY_PASS,
)

pytestmark = pytest.mark.asyncio


async def test_form_success(hass: HomeAssistant):
    """Test successful config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}

    # Mock the SaurClient methods and attributes
    mock_authenticate = AsyncMock(return_value="fake_token")
    mock_get_deliverypoints_data = AsyncMock(
        return_value={
            "meter": {
                "meterBrandCode": "TestManuf",
                "meterModelCode": "TestModel",
                "trueRegistrationNumber": "TestSN",
                "installationDate": "2023-01-01",
            }
        }
    )
    mock_get_lastknown_data = AsyncMock(
        return_value={"readingDate": "2025-01-01T00:00:00", "indexValue": 123}
    )

    # Mock an instance of SaurClient
    mock_client = AsyncMock()
    mock_client.authenticate = mock_authenticate
    mock_client.get_deliverypoints_data = mock_get_deliverypoints_data
    mock_client.get_lastknown_data = mock_get_lastknown_data
    mock_client.default_section_id = "123"
    mock_client.access_token = "fake_token"

    # Mock the coordinator
    coordinator = AsyncMock(spec=SaurCoordinator)
    coordinator.client = mock_client
    coordinator.async_config_entry_first_refresh = AsyncMock()

    # Patch the client creation and coordinator creation
    with (
        patch(
            # Patch the client in config_flow
            "custom_components.eyeonsaur.config_flow.SaurClient",
            return_value=mock_client,
        ),
        patch(
            # Patch the client in coordinator (for calls made in __init__)
            "custom_components.eyeonsaur.coordinator.SaurClient",
            return_value=mock_client,
        ),
        patch(
            # Patch the coordinator creation
            "custom_components.eyeonsaur.coordinator.SaurCoordinator",
            return_value=coordinator,
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                ENTRY_LOGIN: "test@example.com",
                ENTRY_PASS: "password",
                "discovery": True,
            },
        )
        await hass.async_block_till_done()

        assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result2["title"] == "EyeOnSaur - 123"
        assert result2["data"] == {
            "email": "test@example.com",
            "password": "password",
            "discovery": True,
            "token": "fake_token",
            "unique_id": "123",
            "manufacturer": "TestManuf",
            "model": "TestModel",
            "serial_number": "TestSN",
            "created_at": "2023-01-01",
            "absolute_consumption": None,
        }
    # Await the shutdown of the coordinator
    await coordinator.async_shutdown()
    # Move the assertion outside of the with block and await the call
    coordinator.async_shutdown.assert_awaited_once()


async def test_form_invalid_credentials(hass: HomeAssistant):
    """Test config flow with invalid credentials."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}

    # Mock an instance of SaurClient
    mock_client = AsyncMock()
    # Make client.authenticate raise an exception
    mock_client.authenticate.side_effect = Exception("Invalid credentials")

    # Patch the client creation
    with patch(
        "custom_components.eyeonsaur.config_flow.SaurClient",
        return_value=mock_client,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                ENTRY_LOGIN: "test@example.com",
                ENTRY_PASS: "wrong_password",
                "discovery": True,
            },
        )
        await hass.async_block_till_done()

        assert result2["type"] == data_entry_flow.FlowResultType.FORM
        assert result2["errors"] == {"base": "unknown: Invalid credentials"}
