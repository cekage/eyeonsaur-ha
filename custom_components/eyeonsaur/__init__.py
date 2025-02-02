"""Module de configuration pour l'intégration EyeOnSaur dans Home Assistant."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import SaurCoordinator
from .helpers.const import DOMAIN, PLATFORMS
from .helpers.saur_db import SaurDatabaseHelper
from .recorder import SaurRecorder

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EyeOnSaur from a config entry."""

    db_helper = SaurDatabaseHelper(hass)
    recorder = SaurRecorder(hass)

    coordinator = SaurCoordinator(
        hass=hass,
        entry=entry,
        db_helper=db_helper,
        recorder=recorder,
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
    }

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def config_entry_update_listener(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Update listener, called when the config entry options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)
