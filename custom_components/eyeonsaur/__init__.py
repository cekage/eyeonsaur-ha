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
    """Set up the component."""
    hass.data.setdefault(DOMAIN, {})

    db_helper = SaurDatabaseHelper(hass)
    recorder = SaurRecorder(hass)
    coordinator = SaurCoordinator(hass, entry, db_helper, recorder)

    # Store coordinator in a dictionary
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    await coordinator.async_config_entry_first_refresh()

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    # Add listener for config and options updates
    entry.async_on_unload(
        entry.add_update_listener(
            lambda hass, entry: _async_entry_refresher(hass, entry.entry_id)
        )
    )

    return True


async def _async_entry_refresher(hass: HomeAssistant, entry_id: str) -> None:
    """Refresh a config entry."""
    await hass.config_entries.async_reload(entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle unloading of a config entry."""

    # 1. Décharger les plateformes
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )
    if not unload_ok:
        _LOGGER.warning(
            "Problème rencontré lors du déchargement des plateformes"
        )
        return False

    # 2. Arrêter le coordinateur
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    await coordinator.async_shutdown()

    # 3. Supprimer l'entrée du stockage hass.data
    hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
