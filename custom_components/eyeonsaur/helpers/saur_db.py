# pylint: disable=E0401
"""Module de gestion de la base de données pour les consommations Saur."""

import logging
import sqlite3
from datetime import datetime

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


DB_FILE = "consommation_saur.db"


class SaurDatabaseError(Exception):
    """Exception levée lors d'erreurs de base de données Saur."""


class SaurDatabaseHelper:
    """Classe utilitaire pour interagir avec la base de données Saur."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialise le SaurDatabaseHelper.

        Args:
            hass: L'instance de Home Assistant.

        """
        self.hass = hass
        self.db_path = hass.config.path(DB_FILE)

    async def _async_execute_query(
        self,
        query: str,
        params: tuple = (),
    ) -> list[sqlite3.Row] | None:
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

        def execute() -> list[sqlite3.Row] | None:
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
                    return cursor.fetchall()
            except sqlite3.Error as err:
                _LOGGER.exception("Erreur SQLite: %s", err)
                raise SaurDatabaseError(
                    f"Erreur de base de données: {err}"
                ) from err

        return await self.hass.async_add_executor_job(execute)

    async def async_init_db(self) -> None:
        """Initialise la base de données si elle n'existe pas."""
        _LOGGER.info(
            "Création/Mise à jour de la base de données à %s", self.db_path
        )
        await self._async_execute_query(
            """
            CREATE TABLE IF NOT EXISTS consumptions (
                date TEXT PRIMARY KEY,
                relative_value REAL NOT NULL,
                is_ancre INTEGER NOT NULL DEFAULT 0
            );
            """,
        )
        await self._async_execute_query(
            """
            CREATE TABLE IF NOT EXISTS anchor_value (
                date TEXT PRIMARY KEY,
                value REAL NOT NULL
            );
            """,
        )

    async def async_write_consumptions(self, consumptions: list[dict]) -> None:
        """Écrit ou met à jour les consommations dans la base de données.

        Args:
            consumptions: Une liste de dictionnaires contenant les données
                          de consommation.

        """
        _LOGGER.info(
            "Début de la mise à jour des consommations dans la base de données...",
        )
        query = """
            INSERT INTO consumptions (date, relative_value, is_ancre)
            VALUES (?, ?, 0)
            ON CONFLICT(date) DO UPDATE SET
            relative_value = excluded.relative_value
        """

        count = 0
        for conso in consumptions:
            if conso.get("rangeType") == "Day":
                date_str = datetime.fromisoformat(conso["startDate"]).strftime(
                    "%Y-%m-%d %H:%M:%S",
                )
                value = conso.get("value", 0.0)
                _LOGGER.debug(
                    "Préparation de l'insertion/mise à jour de la consommation"
                    " pour date=%s, value=%s",
                    date_str,
                    value,
                )
                await self._async_execute_query(query, (date_str, value))
                count += 1
        _LOGGER.info(
            "Mise à jour de %s consommations dans la base de données.",
            count,
        )

    async def async_update_anchor(self, anchor_data: dict) -> None:
        """Met à jour la valeur d'ancrage dans la base de données.

        Args:
            anchor_data: Un dictionnaire contenant la date de lecture et
                         la valeur de l'index.

        """
        reading_date = datetime.fromisoformat(anchor_data["readingDate"])
        index_value = anchor_data["indexValue"]
        query = """
            INSERT INTO anchor_value (date, value)
            VALUES (?, ?)
            ON CONFLICT(date) DO UPDATE SET value = excluded.value
           """
        await self._async_execute_query(
            query,
            (reading_date.strftime("%Y-%m-%d %H:%M:%S"), index_value),
        )

        _LOGGER.info("Ancre mise à jour dans la base de données.")

    async def async_get_total_consumption(
        self, target_date: datetime
    ) -> float:
        """Récupère la consommation totale jusqu'à une date donnée.

        Args:
            target_date: La date cible pour calculer la consommation totale.

        Returns:
            La consommation totale.

        """
        query = """
           SELECT
                COALESCE(
                (
                    SELECT value
                    FROM anchor_value
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
                            ORDER BY date DESC
                            LIMIT 1
                        )
                        AND date <= ?
                        AND is_ancre = 0
                    ),
                0)
        """
        result = await self._async_execute_query(
            query,
            (target_date.strftime("%Y-%m-%d %H:%M:%S"),),
        )
        return float(result[0][0]) if result and result[0] else 0.0

    async def async_get_all_consumptions_with_absolute(
        self,
    ) -> list[tuple[str, float]]:
        """Récupère toutes les consommations avec leur valeur absolue.

        Returns:
            Une liste de tuples, où chaque tuple contient la date
            (au format 'YYYY-MM-DD HH:MM:SS') et la valeur absolue
            de la consommation.

        """
        _LOGGER.debug("async_get_all_consumptions_with_absolute")

        query = """
            WITH anchor AS (
                SELECT date AS anchor_date, value AS anchor_value
                FROM anchor_value
                ORDER BY date DESC
                LIMIT 1
            )
            SELECT
                c.date,
                CASE
                    WHEN c.date = anchor.anchor_date
                    THEN anchor.anchor_value  -- On utilise uniquement la valeur absolue de l'ancre
                    WHEN c.date > anchor.anchor_date
                    THEN
                        anchor.anchor_value + COALESCE((
                            SELECT SUM(relative_value)
                            FROM consumptions
                            WHERE date >= anchor.anchor_date  -- On inclut la date de l'ancre dans la somme
                            AND date <= c.date
                        ), 0)
                    WHEN c.date < anchor.anchor_date
                    THEN
                        anchor.anchor_value - COALESCE((
                            SELECT SUM(relative_value)
                            FROM consumptions
                            WHERE date > c.date
                            AND date < anchor.anchor_date
                        ), 0)
                END AS absolute_value
            FROM consumptions c
            CROSS JOIN anchor
            ORDER BY c.date DESC;
        """
        results = await self._async_execute_query(query)
        nb_results = len(results) if results else 0
        _LOGGER.info(
            "Récupération de %s consommations avec les valeurs absolues.",
            nb_results,
        )

        formatted_results = []
        if results:
            for row in results:
                date_str = datetime.fromisoformat(row["date"]).strftime(
                    "%Y-%m-%d %H:%M:%S",
                )
                absolute_value = row["absolute_value"]
                formatted_results.append((date_str, absolute_value))

        return formatted_results
