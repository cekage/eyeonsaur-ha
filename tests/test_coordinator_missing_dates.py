"""Test the SaurCoordinator for missing dates."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.eyeonsaur.coordinator import SaurCoordinator

pytestmark = pytest.mark.asyncio


async def test_async_handle_missing_dates(
    hass: HomeAssistant, mock_config_entry, mock_saur_client
):
    """Test handling of missing dates."""
    db_helper = AsyncMock()
    recorder = AsyncMock()
    coordinator = SaurCoordinator(hass, mock_config_entry, db_helper, recorder)
    coordinator.base_data = {}

    # Mock external dependencies
    coordinator.client = mock_saur_client
    mock_saur_client.get_monthly_data.return_value = {
        "consumptions": [
            {
                "rangeType": "Day",
                "startDate": "2024-01-10 00:00:00",
                "value": 1.234,
            }
        ]
    }

    # Mock date utilities
    mock_missing_dates = [(2024, 1, 10), (2024, 1, 12)]
    mock_reduced_missing_dates = [(2024, 1, 10)]

    db_helper.async_get_all_consumptions_with_absolute.return_value = [
        ("2024-01-10 00:00:00", 100.0),
        ("2024-01-12 00:00:00", 102.0),
    ]

    with (
        patch(
            "custom_components.eyeonsaur.coordinator.find_missing_dates",
            return_value=mock_missing_dates,
        ),
        patch(
            "custom_components.eyeonsaur.coordinator.sync_reduce_missing_dates",
            return_value=mock_reduced_missing_dates,
        ),
        patch(
            "custom_components.eyeonsaur.coordinator.asyncio.sleep",
            new_callable=AsyncMock,
        ) as mock_sleep,
    ):
        # Appeler la fonction à tester (indirectement via _async_update_data)
        await coordinator._async_update_data()

        # Injecter manuellement les appels à _async_fetch_periodic_data
        await coordinator._async_fetch_periodic_data(2024, 1, 10)

        # Vérifier que les fonctions de gestion des dates manquantes ont été appelées
        assert (
            coordinator.db_helper.async_get_all_consumptions_with_absolute.call_count
            == 1
        )
        coordinator.recorder.async_inject_historical_data.assert_awaited()
