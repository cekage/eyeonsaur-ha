"""Module définissant la classe SaurDevice pour l'intégration EyeOnSaur."""

from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo

from .helpers.const import (
    DOMAIN,
)


class SaurDevice:
    """Représentation d'un appareil SAUR."""

    def __init__(
        self,
        unique_id: str,
        manufacturer: str,
        model: str,
        serial_number: str,
        created_at: str,
    ):
        """Initialise un appareil SAUR."""
        self.unique_id = unique_id
        self.manufacturer = manufacturer
        self.model = model
        self.serial_number = serial_number
        self.created_at = created_at

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information for this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name="Compteur SAUR",
            manufacturer=self.manufacturer,
            model=self.model,
            serial_number=self.serial_number,
            created_at=self.created_at,
            entry_type=DeviceEntryType.SERVICE,
        )
