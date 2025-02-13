# tests/test_config_flow_ut3.py
"""Tests pour la fonction async_get_deliverypoints_data."""

import aiohttp
import pytest
from aiohttp.client_exceptions import ClientConnectorError
from aiohttp.client_reqrep import ConnectionKey
from homeassistant.core import HomeAssistant
from saur_client import SaurApiError, SaurClient
from unittest.mock import MagicMock

from custom_components.eyeonsaur.config_flow import (
    async_get_deliverypoints_data,
)


async def test_async_get_deliverypoints_data_success(
    hass: HomeAssistant, mocker
) -> None:
    """Test successful data retrieval."""
    mock_client = mocker.AsyncMock(spec=SaurClient)
    mock_client.get_deliverypoints_data.return_value = {"delivery_points": []}

    result = await async_get_deliverypoints_data(mock_client)
    assert result == {"delivery_points": []}
    mock_client.get_deliverypoints_data.assert_called_once()


async def test_async_get_deliverypoints_data_saur_api_error_unauthorized(
    hass: HomeAssistant, mocker
) -> None:
    """Test SaurApiError with unauthorized message."""
    mock_client = mocker.AsyncMock(spec=SaurClient)
    mock_client.get_deliverypoints_data.side_effect = SaurApiError(
        "Unauthorized"
    )
    with pytest.raises(SaurApiError, match="Unauthorized"):
        await async_get_deliverypoints_data(mock_client)
    mock_client.get_deliverypoints_data.assert_called_once()


async def test_async_get_deliverypoints_data_saur_api_error_other(
    hass: HomeAssistant, mocker
) -> None:
    """Test SaurApiError with a different message."""
    mock_client = mocker.AsyncMock(spec=SaurClient)
    mock_client.get_deliverypoints_data.side_effect = SaurApiError(
        "Some error"
    )

    with pytest.raises(SaurApiError, match="Some error"):
        await async_get_deliverypoints_data(mock_client)
    mock_client.get_deliverypoints_data.assert_called_once()


async def test_async_get_deliverypoints_data_client_connector_error(
    hass: HomeAssistant, mocker
) -> None:
    """Test ClientConnectorError."""
    mock_client = mocker.AsyncMock(spec=SaurClient)
    mock_client.get_deliverypoints_data.side_effect = ClientConnectorError(
        connection_key=ConnectionKey(
            host="test_host",
            port=8080,
            ssl=False,
            proxy=None,
            proxy_auth=None,
            proxy_headers_hash=None,
            is_ssl=None,
        ),
        os_error=OSError("Simulated connection error"),
    )

    with pytest.raises(ClientConnectorError):
        await async_get_deliverypoints_data(mock_client)
    mock_client.get_deliverypoints_data.assert_called_once()
