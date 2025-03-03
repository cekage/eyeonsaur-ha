# tests/test_saur_db.py
import asyncio
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Final

import pytest
from homeassistant.core import HomeAssistant

from custom_components.eyeonsaur.helpers.saur_db import (
    SaurDatabaseError,
    SaurDatabaseHelper,
)
from custom_components.eyeonsaur.models import (
    ConsumptionData,
    ConsumptionDatas,
    RelevePhysique,
    SaurSqliteResponse,
    SectionId,
    StrDate,
    TheoreticalConsumptionDatas,
)

DB_FILE = "test_consommation_saur.db"
TEST_ENTRY_ID = "test_entry_id"
TEST_SECTION_ID: Final[SectionId] = SectionId("test_section_id")
TEST_SECTION_ID_2: Final[SectionId] = SectionId(
    "test_section_id_2"
)  # Nouveau section_id


pytestmark = pytest.mark.asyncio


@asynccontextmanager
async def temp_db(
    hass: HomeAssistant, db_file: str
) -> AsyncGenerator[SaurDatabaseHelper, None]:
    """Context manager for creating and cleaning up a test database."""
    db_helper = SaurDatabaseHelper(hass, TEST_ENTRY_ID)
    db_helper.db_path = db_file

    # Supprimer la base de données si elle existe
    if os.path.exists(db_helper.db_path):
        os.remove(db_helper.db_path)

    # initialiser la base
    await db_helper.async_init_db()

    try:
        yield db_helper
    finally:
        # Ensure connection is closed and db file is removed even if tests fail
        try:
            await db_helper._async_execute_query(
                "SELECT 1"
            )  # Simple query to ensure connection is closed

        except Exception as e:
            print(
                f"Error while closing db connection: {e}"
            )  # Debug closing errors
        finally:
            if os.path.exists(db_helper.db_path):
                try:
                    os.remove(db_helper.db_path)
                except Exception as e:
                    print(
                        f"Error deleting db file: {e}"
                    )  # Debug delete errors


@pytest.fixture(name="db_helper")
async def db_helper_fixture(
    hass: HomeAssistant,
) -> AsyncGenerator[SaurDatabaseHelper, None]:
    """Fixture to create a SaurDatabaseHelper instance with a temporary database."""
    async with temp_db(hass, DB_FILE) as db_helper:
        # Vider les tables avant chaque test
        await db_helper._async_execute_query("DELETE FROM consumptions")
        await db_helper._async_execute_query("DELETE FROM anchor_value")

        # Ajouter des données pour TEST_SECTION_ID
        consumptions_1 = ConsumptionDatas(
            [
                ConsumptionData(
                    startDate=StrDate("2024-10-19 00:00:00"),
                    value=0.51,
                    rangeType="Day",
                ),
                ConsumptionData(
                    startDate=StrDate("2024-10-20 00:00:00"),
                    value=0.5,
                    rangeType="Day",
                ),
                ConsumptionData(
                    startDate=StrDate("2024-10-21 00:00:00"),
                    value=0.82,
                    rangeType="Day",
                ),
                ConsumptionData(
                    startDate=StrDate("2024-10-22 00:00:00"),
                    value=0.42,
                    rangeType="Day",
                ),
            ]
        )
        await db_helper.async_write_consumptions(
            consumptions_1, TEST_SECTION_ID
        )
        anchor_data_1 = RelevePhysique(
            date=StrDate("2024-10-21 00:00:00"), valeur=114.0
        )
        await db_helper.async_update_anchor(anchor_data_1, TEST_SECTION_ID)

        # Ajouter des données pour TEST_SECTION_ID_2
        consumptions_2 = ConsumptionDatas(
            [
                ConsumptionData(
                    startDate=StrDate("2024-10-19 00:00:00"),
                    value=0.3,
                    rangeType="Day",
                ),
                ConsumptionData(
                    startDate=StrDate("2024-10-20 00:00:00"),
                    value=0.2,
                    rangeType="Day",
                ),
                ConsumptionData(
                    startDate=StrDate("2024-10-21 00:00:00"),
                    value=0.1,
                    rangeType="Day",
                ),
                ConsumptionData(
                    startDate=StrDate("2024-10-22 00:00:00"),
                    value=0.4,
                    rangeType="Day",
                ),
            ]
        )
        await db_helper.async_write_consumptions(
            consumptions_2, TEST_SECTION_ID_2
        )
        anchor_data_2 = RelevePhysique(
            date=StrDate("2024-10-21 00:00:00"), valeur=50.0
        )
        await db_helper.async_update_anchor(anchor_data_2, TEST_SECTION_ID_2)

        yield db_helper


async def test_async_init_db(db_helper: SaurDatabaseHelper) -> None:
    """Test async_init_db."""
    # Appeler explicitement async_init_db dans le test
    await db_helper.async_init_db()
    # Vérifie que la base de données est initialisée
    # en exécutant une requête simple
    await db_helper._async_execute_query("SELECT 1")


async def test_async_write_consumptions(db_helper: SaurDatabaseHelper) -> None:
    """Test async_write_consumptions."""
    await db_helper._async_execute_query("DELETE FROM consumptions")
    await db_helper._async_execute_query("DELETE FROM anchor_value")
    consumptions: ConsumptionDatas = ConsumptionDatas(
        [
            ConsumptionData(
                startDate=StrDate("2024-01-01 00:00:00"),
                value=1.0,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-01-02 00:00:00"),
                value=2.0,
                rangeType="Day",
            ),
        ]
    )
    await db_helper.async_write_consumptions(
        consumptions, TEST_SECTION_ID
    )  # Pass section_id

    # Vérifier que les données sont bien écrites dans la base
    rows: SaurSqliteResponse = await db_helper._async_execute_query(
        "SELECT * FROM consumptions"
    )
    assert rows is not None
    assert len(rows) == 2
    assert rows[0]["date"] == "2024-01-01 00:00:00"
    assert rows[0]["relative_value"] == 1.0
    assert rows[0]["section_id"] == TEST_SECTION_ID
    assert rows[1]["date"] == "2024-01-02 00:00:00"
    assert rows[1]["relative_value"] == 2.0
    assert rows[1]["section_id"] == TEST_SECTION_ID


async def test_async_update_anchor(db_helper: SaurDatabaseHelper) -> None:
    """Test async_update_anchor."""
    anchor_data: RelevePhysique = RelevePhysique(
        date=StrDate("2024-01-01 00:00:00"), valeur=100
    )
    await db_helper._async_execute_query(
        "DELETE FROM anchor_value"
    )  # Ajout de cette ligne

    await db_helper.async_update_anchor(
        anchor_data, TEST_SECTION_ID
    )  # Pass section_id

    # Vérifier que l'ancre est bien écrite dans la base
    rows: SaurSqliteResponse = await db_helper._async_execute_query(
        "SELECT * FROM anchor_value"
    )
    assert rows is not None
    assert len(rows) == 1
    assert rows[0]["date"] == "2024-01-01 00:00:00"
    assert rows[0]["section_id"] == TEST_SECTION_ID
    assert rows[0]["value"] == 100


async def test_async_get_total_consumption(
    db_helper: SaurDatabaseHelper,
) -> None:
    """Test async_get_total_consumption."""
    # Préparer des données de test
    consumptions: ConsumptionDatas = ConsumptionDatas(
        [
            ConsumptionData(
                startDate=StrDate("2024-10-19 00:00:00"),
                value=0.51,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-20 00:00:00"),
                value=0.50,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-21 00:00:00"),
                value=0.82,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-22 00:00:00"),
                value=0.42,
                rangeType="Day",
            ),
        ]
    )

    anchor_data: RelevePhysique = RelevePhysique(
        date=StrDate("2024-10-21 00:00:00"),
        valeur=114.0,
    )

    await db_helper.async_write_consumptions(consumptions, TEST_SECTION_ID)
    await db_helper.async_update_anchor(anchor_data, TEST_SECTION_ID)

    # Appeler la fonction à tester
    total_consumption = await db_helper.async_get_total_consumption(
        datetime(2024, 1, 3),
        TEST_SECTION_ID,  # Pass section_id
    )

    # Vérifier le résultat
    assert total_consumption == 114.0


async def test_async_get_all_consumptions_with_absolute2(
    db_helper: SaurDatabaseHelper,
) -> None:
    """Test async_get_all_consumptions_with_absolute with real values."""
    # Appeler la fonction à tester
    result: TheoreticalConsumptionDatas = (
        await db_helper.async_get_all_consumptions_with_absolute(
            TEST_SECTION_ID
        )
    )  # Pass section_id

    # Vérifier le résultat (ordre inverse des dates car ORDER BY c.date DESC)
    assert len(result) == 4
    assert result[0].date == "2024-10-22 00:00:00"
    assert result[0].indexValue == 114.42
    assert result[1].date == "2024-10-21 00:00:00"
    assert result[1].indexValue == 114.0
    assert result[2].date == "2024-10-20 00:00:00"
    assert result[2].indexValue == 113.18  # Corrected value
    assert result[3].date == "2024-10-19 00:00:00"
    assert result[3].indexValue == 112.68  # Corrected value


async def test_async_get_all_consumptions_with_absolute3(
    db_helper: SaurDatabaseHelper,
) -> None:
    """Test async_get_all_consumptions_with_absolute with real data."""

    # Préparer les données de test dans la base de données
    consumptions = ConsumptionDatas(
        [
            ConsumptionData(
                startDate=StrDate("2024-10-01 00:00:00"),
                value=0.54,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-02 00:00:00"),
                value=0.61,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-03 00:00:00"),
                value=0.61,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-04 00:00:00"),
                value=0.60,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-05 00:00:00"),
                value=0.62,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-06 00:00:00"),
                value=0.94,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-07 00:00:00"),
                value=0.86,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-08 00:00:00"),
                value=0.98,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-09 00:00:00"),
                value=0.69,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-10 00:00:00"),
                value=0.49,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-11 00:00:00"),
                value=0.63,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-12 00:00:00"),
                value=0.88,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-13 00:00:00"),
                value=0.78,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-14 00:00:00"),
                value=0.94,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-15 00:00:00"),
                value=0.74,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-16 00:00:00"),
                value=0.78,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-17 00:00:00"),
                value=0.61,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-18 00:00:00"),
                value=0.82,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-19 00:00:00"),
                value=0.51,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-20 00:00:00"),
                value=0.50,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-21 00:00:00"),
                value=0.82,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-22 00:00:00"),
                value=0.42,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-23 00:00:00"),
                value=0.42,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-24 00:00:00"),
                value=0.36,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-25 00:00:00"),
                value=0.48,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-26 00:00:00"),
                value=0.53,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-27 00:00:00"),
                value=0.99,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-28 00:00:00"),
                value=0.91,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-29 00:00:00"),
                value=0.98,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-30 00:00:00"),
                value=0.86,
                rangeType="Day",
            ),
            ConsumptionData(
                startDate=StrDate("2024-10-31 00:00:00"),
                value=0.48,
                rangeType="Day",
            ),
        ]
    )

    anchor_data = RelevePhysique(
        date=StrDate("2024-10-21 00:00:00"), valeur=114.0
    )

    await db_helper.async_write_consumptions(consumptions, TEST_SECTION_ID)
    await db_helper.async_update_anchor(anchor_data, TEST_SECTION_ID)

    # Appeler la fonction à tester
    result: TheoreticalConsumptionDatas = (
        await db_helper.async_get_all_consumptions_with_absolute(
            TEST_SECTION_ID
        )
    )

    # Vérifier le résultat
    assert len(result) == 31

    expected_values = {
        "2024-10-01 00:00:00": 99.59,
        "2024-10-02 00:00:00": 100.20,
        "2024-10-03 00:00:00": 100.81,
        "2024-10-04 00:00:00": 101.41,
        "2024-10-05 00:00:00": 102.03,
        "2024-10-06 00:00:00": 102.97,
        "2024-10-07 00:00:00": 103.83,
        "2024-10-08 00:00:00": 104.81,
        "2024-10-09 00:00:00": 105.50,
        "2024-10-10 00:00:00": 105.99,
        "2024-10-11 00:00:00": 106.62,
        "2024-10-12 00:00:00": 107.50,
        "2024-10-13 00:00:00": 108.28,
        "2024-10-14 00:00:00": 109.22,
        "2024-10-15 00:00:00": 109.96,
        "2024-10-16 00:00:00": 110.74,
        "2024-10-17 00:00:00": 111.35,
        "2024-10-18 00:00:00": 112.17,
        "2024-10-19 00:00:00": 112.68,
        "2024-10-20 00:00:00": 113.18,
        "2024-10-21 00:00:00": 114.00,
        "2024-10-22 00:00:00": 114.42,
        "2024-10-23 00:00:00": 114.84,
        "2024-10-24 00:00:00": 115.20,
        "2024-10-25 00:00:00": 115.68,
        "2024-10-26 00:00:00": 116.21,
        "2024-10-27 00:00:00": 117.20,
        "2024-10-28 00:00:00": 118.11,
        "2024-10-29 00:00:00": 119.09,
        "2024-10-30 00:00:00": 119.95,
        "2024-10-31 00:00:00": 120.43,
    }
    # Inverser l'ordre des clés pour correspondre à l'ORDER BY DESC
    ordered_dates = list(expected_values.keys())[::-1]

    for i, row in enumerate(result):
        expected_date = ordered_dates[i]
        assert str(row.date) == expected_date
        assert row.indexValue == pytest.approx(expected_values[expected_date])
