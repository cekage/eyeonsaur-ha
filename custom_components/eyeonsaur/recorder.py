"""Module d'injection de données historiques dans le recorder de Home Assistant."""

# pylint: disable=E0401

import logging
from datetime import datetime, timedelta

from homeassistant.components import recorder
from homeassistant.components.recorder.statistics import (
    StatisticData,
    StatisticMetaData,
    async_import_statistics,
)
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.util.dt import as_local

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


class SaurRecorder:
    """Service pour injecter des données.

    Service d'injection historiques dans le
    recorder de Home Assistant."""

    __skip__ = True  # Alternative pour ignorer le warning

    def __init__(self, hass: HomeAssistant, entry=None):
        """Initialiser le service."""
        self.hass = hass
        self.entry = entry
        self.entity_id = ""
        self._recorder = None

    async def async_inject_historical_data(
        self,
        entity_id: str,
        date: datetime,
        value: float,
    ) -> None:
        """Injecte des données historiques pour un capteur spécifique."""
        _LOGGER.info(
            "Injecting historical data for {%s} at {%s} with value {%s}",
            entity_id,
            date,
            value,
        )
        if self._recorder is None:
            self._recorder = recorder.get_instance(self.hass)

        self.entity_id = "sensor.compteur_saur_" + entity_id

        epoch = datetime(1970, 1, 1, 0, 0, 0)
        epoch = as_local(epoch)
        start_of_day = datetime(date.year, date.month, date.day, 1, 0, 0)
        start_of_day = as_local(start_of_day)
        end_of_day = datetime(date.year, date.month, date.day, 23, 59, 59)
        end_of_day = as_local(end_of_day)

        statistic_id = self.entity_id

        metadata = StatisticMetaData(
            has_mean=False,
            has_sum=True,
            name=f"EyeOnSaur Consumption of {self.entity_id}",
            source="recorder",
            statistic_id=statistic_id,
            unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        )

        interval = timedelta(hours=1)
        stats = []
        current_time = start_of_day + 0 * interval
        _LOGGER.info(
            " 📜 for %s at %s with value %s",
            self.entity_id,
            current_time,
            value,
        )
        stats.append(
            StatisticData(
                start=current_time,
                last_reset=epoch,
                sum=value,
            ),
        )
        async_import_statistics(self.hass, metadata, stats)

        _LOGGER.info(
            "Injected historical data for %s at %s with value %s",
            self.entity_id,
            date,
            value,
        )
