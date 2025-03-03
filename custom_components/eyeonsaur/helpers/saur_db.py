# pylint: disable=E0401
"""Module de gestion de la base de données pour les consommations Saur."""

import logging
import sqlite3
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant

from ..models import (
    ConsumptionDatas,
    RelevePhysique,
    SaurSqliteResponse,
    SectionId,
    StrDate,
    TheoreticalConsumptionData,
    TheoreticalConsumptionDatas,
)

_LOGGER = logging.getLogger(__name__)


class SaurDatabaseError(Exception):
    """Exception levée lors d'erreurs de base de données Saur."""


class SaurDatabaseHelper:
    """Classe utilitaire pour interagir avec la base de données Saur."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialise le SaurDatabaseHelper.

        Args:
            hass: L'instance de Home Assistant.
            entry_id: L'ID de l'entrée de configuration.

        """
        self.hass = hass
        self.db_file = f"consommation_saur_{entry_id}.db"
        self.db_path = hass.config.path(self.db_file)

    async def _async_execute_query(
        self,
        query: str,
        params: Sequence[Any] = (),
    ) -> SaurSqliteResponse:
        """Exécute une requête SQL de manière asynchrone.

        Args:
            query: La requête SQL à exécuter.
            params: Les paramètres à passer à la requête.

        Returns:
            Les résultats de la requête, si applicables.

        Raises:
            SaurDatabaseError: En cas d'erreur lors de l'exécution
                               de la requête.

        """

        def execute() -> SaurSqliteResponse:
            """Exécute la requête SQL dans un thread."""
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    _LOGGER.debug(
                        "Exécution de la requête SQL: %s avec params : %s",
                        query,
                        params,
                    )
                    cursor.execute(query, params)
                    conn.commit()
                    result = cursor.fetchall()
                    return tuple(result) if result else None

            except sqlite3.Error as err:
                _LOGGER.exception("Erreur SQLite: %s", err)
                raise SaurDatabaseError(
                    f"Erreur de base de données: {err}"
                ) from err

        return await self.hass.async_add_executor_job(execute)

    async def async_init_db(self) -> None:
        """Initialise la base de données si elle n'existe pas."""
        _LOGGER.debug(
            "Création/Mise à jour de la base de données à %s", self.db_path
        )
        await self._async_execute_query(
            """
            CREATE TABLE IF NOT EXISTS consumptions (
                date TEXT NOT NULL,
                section_id TEXT NOT NULL,
                relative_value REAL NOT NULL,
                is_ancre INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (date, section_id)
            );
            """,
        )
        await self._async_execute_query(
            """
            CREATE TABLE IF NOT EXISTS anchor_value (
                date TEXT NOT NULL,
                section_id TEXT NOT NULL,
                value REAL NOT NULL,
                PRIMARY KEY (date, section_id)
            );
            """,
        )

    async def async_write_consumptions(
        self, consumptions: ConsumptionDatas, section_id: SectionId
    ) -> None:
        """Écrit ou met à jour les consommations dans la base de données.

        Args:
            consumptions: Une liste de dictionnaires contenant les données
                          de consommation.
            section_id: L'identifiant unique du compteur.

        """
        _LOGGER.debug(
            "Début de la mise à jour des consommations dans la bdd pour %s",
            section_id,
        )
        query = """
            INSERT INTO consumptions (date, section_id,
                relative_value, is_ancre)
            VALUES (?, ?, ?, 0)
            ON CONFLICT(date, section_id) DO UPDATE SET
            relative_value = excluded.relative_value
        """

        count = 0
        for conso in consumptions:
            if conso.rangeType == "Day":
                date_str = datetime.fromisoformat(conso.startDate).strftime(
                    "%Y-%m-%d %H:%M:%S",
                )
                value = conso.value
                _LOGGER.debug(
                    "Préparation de l'insertion/mise à jour de la consommation"
                    " pour date=%s, value=%s, section_id=%s",
                    date_str,
                    value,
                    section_id,
                )
                await self._async_execute_query(
                    query, (date_str, section_id, value)
                )
                count += 1
        _LOGGER.debug(
            "Mise à jour de %s consommations dans la base de données pour %s.",
            count,
            section_id,
        )

    async def async_update_anchor(
        self, releve: RelevePhysique, section_id: SectionId
    ) -> None:
        """Met à jour la valeur d'ancrage dans la base de données.

        Args:
            releve: Les données du relevé physique.
            section_id: L'identifiant unique du compteur.

        """
        reading_date = datetime.fromisoformat(releve.date)
        index_value = releve.valeur
        query = """
            INSERT INTO anchor_value (date, section_id, value)
            VALUES (?, ?, ?)
            ON CONFLICT(date, section_id) DO UPDATE SET value = excluded.value
           """
        await self._async_execute_query(
            query,
            (
                reading_date.strftime("%Y-%m-%d %H:%M:%S"),
                section_id,
                index_value,
            ),
        )

        _LOGGER.info(
            "Ancre mise à jour dans la base de données pour %s.", section_id
        )

    async def async_get_total_consumption(
        self, target_date: datetime, section_id: SectionId
    ) -> float:
        """Récupère la consommation totale jusqu'à une date donnée.

        Args:
            target_date: La date cible pour calculer la consommation totale.
            section_id: L'identifiant unique du compteur.

        Returns:
            La consommation totale.

        """
        query = """
           SELECT
                COALESCE(
                (
                    SELECT value
                    FROM anchor_value
                    WHERE section_id = ?
                    ORDER BY date DESC
                    LIMIT 1
                ), 0
                )
                + COALESCE(
                    (
                        SELECT SUM(relative_value)
                        FROM consumptions
                        WHERE date > (
                            SELECT date
                            FROM anchor_value
                            WHERE section_id = ?
                            ORDER BY date DESC
                            LIMIT 1
                        )
                        AND date <= ?
                        AND section_id = ?
                        AND is_ancre = 0
                    ),
                0)
        """
        result = await self._async_execute_query(
            query,
            (
                section_id,
                section_id,
                target_date.strftime("%Y-%m-%d %H:%M:%S"),
                section_id,
            ),
        )
        return float(result[0][0]) if result and result[0] else 0.0

    async def async_get_all_consumptions_with_absolute(
        self, section_id: SectionId
    ) -> TheoreticalConsumptionDatas:
        """
        Récupère toutes les consommations avec leur valeur
        absolue en utilisant une seule requête SQL.

        Args:
            section_id: L'identifiant unique du compteur.

        Returns:
            Une liste de TheoreticalConsumptionData.
        """

        _LOGGER.debug(
            "async_get_all_consumptions_with_absolute pour %s", section_id
        )

        query = """
            WITH Anchor AS (
            SELECT date, value FROM anchor_value
            WHERE section_id = ?
            ),
            CumulativeConsumptions AS (
            SELECT c.date, c.relative_value,
                SUM(c.relative_value) OVER (ORDER BY c.date ASC)
                AS cumulative_relative
            FROM consumptions c WHERE c.section_id = ?
            )
            SELECT cc.date, cc.relative_value,
            CASE
                WHEN cc.date = (SELECT date FROM Anchor)
                THEN (SELECT value FROM Anchor)
                ELSE (SELECT value FROM Anchor) - (
                SELECT cumulative_relative FROM CumulativeConsumptions
                WHERE date = (SELECT date FROM Anchor))
                + cc.cumulative_relative
            END AS absolue
            FROM CumulativeConsumptions cc
            ORDER BY cc.date DESC;
        """

        results = await self._async_execute_query(
            query, (section_id, section_id)
        )

        nb_results = len(results) if results else 0
        _LOGGER.debug(
            "Récupération de %s consommations avec les "
            "valeurs absolues pour %s.",
            nb_results,
            section_id,
        )

        formatted_results: TheoreticalConsumptionDatas = (
            TheoreticalConsumptionDatas([])
        )  # Assuming this is how you create an empty object

        if results:
            for row in results:
                try:
                    date_str: StrDate = StrDate(
                        datetime.fromisoformat(row["date"]).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    )
                    absolute_value: float = float(row["absolue"])

                    data_point: TheoreticalConsumptionData = (
                        TheoreticalConsumptionData(
                            date=date_str, indexValue=absolute_value
                        )
                    )
                    formatted_results.append(
                        data_point
                    )  # Assuming append is the correct method
                except ValueError as e:
                    print(f"⚠️ Date invalide détectée : {row['date']} -> {e}")
                except Exception as e:
                    print(
                        "⚠️ Erreur lors de la création du "
                        f"TheoreticalConsumptionData : {e}"
                    )

        return formatted_results
