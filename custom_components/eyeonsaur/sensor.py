"""Module de gestion du capteur pour l'intégration EyeOnSaur."""

# pylint: disable=E0401

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import SaurCoordinator
from .device import SaurDevice
from .helpers.const import (
    DOMAIN,
    ENTRY_CREATED_AT,
    ENTRY_MANUFACTURER,
    ENTRY_MODEL,
    ENTRY_SERIAL_NUMBER,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure la plateforme de capteur via un config flow."""
    _LOGGER.info("Configuration de la plateforme de capteur via config flow.")

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    device = SaurDevice(
        unique_id=coordinator.client.default_section_id,
        manufacturer=entry.data.get(ENTRY_MANUFACTURER),
        model=entry.data.get(ENTRY_MODEL),
        serial_number=entry.data.get(ENTRY_SERIAL_NUMBER),
        created_at=entry.data.get(ENTRY_CREATED_AT),
    )
    sensor = SaurSensor(coordinator, device)
    async_add_entities([sensor], update_before_add=True)
    _LOGGER.info("Capteur ajouté à Home Assistant.")


class SaurSensor(CoordinatorEntity[SaurCoordinator], SensorEntity):
    """Représentation d'un capteur de consommation d'eau SAUR."""

    _attr_has_entity_name = True  # Formatage automatique du nom
    _attr_translation_key = "water_consumption"  # Prépare la localisation
    _attr_device_class = SensorDeviceClass.WATER
    _attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS
    _attr_state_class = (
        SensorStateClass.TOTAL_INCREASING
    )  # Utilisation de l'énumération
    _attr_suggested_display_precision = 0

    def __init__(
        self,
        coordinator: SaurCoordinator,
        device: SaurDevice,
    ) -> None:
        """Initialise le capteur."""
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = f"{coordinator.client.default_section_id}_water"
        self._initial_consumption = 0.0

    @property
    def device_info(self) -> DeviceInfo:
        """Retourne les informations sur l'appareil."""
        return self._device.device_info

    @property
    def name(self) -> str | None:
        """Retourne le nom du capteur."""
        return f"{self.coordinator.client.default_section_id}"

    @property
    def native_value(self) -> None:
        """Retourne toujours None pour ne pas interferer avec Statistics."""

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state of the sensor."""
        return {
            "state_class": "total_increasing",
            "physical_meter_date": self.coordinator.data.get(
                "releve_physique",
                {},
            ).get("date"),
            "releve_physique_volume": self.coordinator.data.get(
                "releve_physique",
                {},
            ).get("valeur"),
            "installation_date": self.coordinator.data.get("created_at"),
        }
