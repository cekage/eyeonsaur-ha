"""Tests for the EyeOnSaur recorder."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util.dt import as_local

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def mock_recorder_module():
    """Mock the recorder module."""
    with (
        patch(
            "custom_components.eyeonsaur.recorder.recorder", new_callable=Mock
        ),
        patch("custom_components.eyeonsaur.recorder.async_import_statistics"),
        patch(
            "custom_components.eyeonsaur.recorder.StatisticData",
            new_callable=Mock,
        ),
        patch(
            "custom_components.eyeonsaur.recorder.StatisticMetaData",
            new_callable=Mock,
        ),
    ):
        yield


from custom_components.eyeonsaur.recorder import (
    SaurRecorder,  # pylint: disable=wrong-import-position
)


async def test_async_inject_historical_data(hass: HomeAssistant) -> None:
    """Test async_inject_historical_data."""
    # Initialiser SaurRecorder
    saur_recorder = SaurRecorder(hass)

    # Définir des données de test
    entity_id = "123"
    date = as_local(datetime(2024, 1, 10))
    value = 100.5

    # Appeler la fonction à tester
    await saur_recorder.async_inject_historical_data(entity_id, date, value)
