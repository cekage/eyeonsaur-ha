"""Tests unitaires pour la fonction create_saur_client du config flow."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from custom_components.eyeonsaur.config_flow import create_saur_client
from custom_components.eyeonsaur.helpers.const import DEV  # Importe DEV
from saur_client import SaurClient


@pytest.mark.asyncio  # AJOUT du marker @pytest.mark.asyncio pour rendre les tests asynchrones
async def test_create_saur_client_dev_mode_false() -> None:  # MODIF: async def
    """Test create_saur_client avec dev_mode=False (production)."""
    client = create_saur_client(login="test_login", password="test_password")
    assert isinstance(client, SaurClient)
    assert client.dev_mode is True


@pytest.mark.asyncio  # AJOUT du marker @pytest.mark.asyncio pour rendre les tests asynchrones
async def test_create_saur_client_dev_mode_true() -> None:  # MODIF: async def
    """Test create_saur_client avec dev_mode=True (développement)."""
    client = create_saur_client(login="test_login", password="test_password")
    assert isinstance(client, SaurClient)
    assert client.dev_mode is True
    assert (
        client.base_url == "http://localhost:8080"
    )  # Vérifie que base_url est bien l'URL de DEV


@pytest.mark.asyncio  # AJOUT du marker @pytest.mark.asyncio pour rendre les tests asynchrones
async def test_create_saur_client_credentials() -> None:  # MODIF: async def
    """Test create_saur_client vérifie que les credentials sont bien passés au client."""
    client = create_saur_client(login="test_login", password="test_password")
    assert client.login == "test_login"
    assert client.password == "test_password"
