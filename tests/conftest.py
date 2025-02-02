"""Fixtures for the EyeOnSaur integration tests."""

from unittest.mock import patch

import pytest


# Fixture loading the integration
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    return


# Fixture loading the manifest.json
@pytest.fixture(autouse=True)
def mock_manifest(hass):
    """Mock the manifest.json file."""
    with patch(
        "pytest_homeassistant_custom_component.common.get_test_config_dir",
        return_value="custom_components/eyeonsaur",
    ):
        yield
