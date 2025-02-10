"""Tests for the EyeOnSaur saur_db module."""

from datetime import datetime

import pytest
from homeassistant.core import HomeAssistant

from custom_components.eyeonsaur.helpers.saur_db import (
    SaurDatabaseError,
    SaurDatabaseHelper,
)

DB_FILE = "test_consommation_saur.db"

pytestmark = pytest.mark.asyncio


@pytest.fixture(name="db_helper")
async def db_helper_fixture(hass: HomeAssistant) -> SaurDatabaseHelper:
    """Fixture to create a SaurDatabaseHelper instance."""
    db_helper = SaurDatabaseHelper(hass)
    db_helper.db_path = DB_FILE

    # initialiser la base
    await db_helper.async_init_db()

    # Vider les tables avant chaque test
    await db_helper._async_execute_query("DELETE FROM consumptions")
    await db_helper._async_execute_query("DELETE FROM anchor_value")

    yield db_helper

    # Fermer la connexion après chaque test en exécutant une requête simple
    await db_helper._async_execute_query("SELECT 1")


async def test_async_init_db(db_helper: SaurDatabaseHelper):
    """Test async_init_db."""
    # Appeler explicitement async_init_db dans le test
    await db_helper.async_init_db()
    # Vérifie que la base de données est initialisée
    # en exécutant une requête simple
    await db_helper._async_execute_query("SELECT 1")


async def test_async_write_consumptions(db_helper: SaurDatabaseHelper):
    """Test async_write_consumptions."""
    consumptions = [
        {"startDate": "2024-01-01 00:00:00", "value": 1.0, "rangeType": "Day"},
        {"startDate": "2024-01-02 00:00:00", "value": 2.0, "rangeType": "Day"},
    ]
    await db_helper.async_write_consumptions(consumptions)

    # Vérifier que les données sont bien écrites dans la base
    rows = await db_helper._async_execute_query("SELECT * FROM consumptions")
    assert len(rows) == 2
    assert rows[0]["date"] == "2024-01-01 00:00:00"
    assert rows[0]["relative_value"] == 1.0
    assert rows[1]["date"] == "2024-01-02 00:00:00"
    assert rows[1]["relative_value"] == 2.0


async def test_async_update_anchor(db_helper: SaurDatabaseHelper):
    """Test async_update_anchor."""
    anchor_data = {"readingDate": "2024-01-01 00:00:00", "indexValue": 100}
    await db_helper.async_update_anchor(anchor_data)

    # Vérifier que l'ancre est bien écrite dans la base
    rows = await db_helper._async_execute_query("SELECT * FROM anchor_value")
    assert len(rows) == 1
    assert rows[0]["date"] == "2024-01-01 00:00:00"
    assert rows[0]["value"] == 100


async def test_async_get_total_consumption(db_helper: SaurDatabaseHelper):
    """Test async_get_total_consumption."""
    # Préparer des données de test
    consumptions = [
        {"startDate": "2024-01-01 00:00:00", "value": 1.0, "rangeType": "Day"},
        {"startDate": "2024-01-02 00:00:00", "value": 2.0, "rangeType": "Day"},
    ]
    anchor_data = {"readingDate": "2023-12-31 00:00:00", "indexValue": 100}

    await db_helper.async_write_consumptions(consumptions)
    await db_helper.async_update_anchor(anchor_data)

    # Appeler la fonction à tester
    total_consumption = await db_helper.async_get_total_consumption(
        datetime(2024, 1, 3)
    )

    # Vérifier le résultat
    assert total_consumption == 103.0


async def test_async_get_all_consumptions_with_absolute(
    db_helper: SaurDatabaseHelper,
):
    """Test async_get_all_consumptions_with_absolute."""
    # Préparer des données de test
    consumptions = [
        {"startDate": "2024-01-01 00:00:00", "value": 1.0, "rangeType": "Day"},
        {"startDate": "2024-01-02 00:00:00", "value": 2.0, "rangeType": "Day"},
        {"startDate": "2024-01-03 00:00:00", "value": 3.0, "rangeType": "Day"},
    ]
    anchor_data = {"readingDate": "2024-01-02 00:00:00", "indexValue": 100}

    await db_helper.async_write_consumptions(consumptions)
    await db_helper.async_update_anchor(anchor_data)
    # Appeler la fonction à tester
    result = await db_helper.async_get_all_consumptions_with_absolute()

    # Vérifier le résultat
    assert len(result) == 3
    assert result[0][0] == "2024-01-03 00:00:00"
    assert result[0][1] == 105.0
    assert result[1][0] == "2024-01-02 00:00:00"
    assert result[1][1] == 102.0
    assert result[2][0] == "2024-01-01 00:00:00"
    assert result[2][1] == 100.0


async def test_async_execute_query_exception(db_helper: SaurDatabaseHelper):
    """Test that async_execute_query raises SaurDatabaseError on query error."""
    with pytest.raises(SaurDatabaseError, match="no such table"):
        await db_helper._async_execute_query(
            "SELECT * FROM non_existent_table"
        )


# Assurez-vous de supprimer le fichier de base de données après tous les tests
# def teardown_module(module):
#     """Supprime le fichier de base de données après tous les tests."""
#     if os.path.exists(DB_FILE):
#         os.remove(DB_FILE)
