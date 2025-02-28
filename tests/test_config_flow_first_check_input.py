"""Tests unitaires pour la fonction first_check_input du config flow."""

import pytest

from custom_components.eyeonsaur.config_flow import first_check_input
from custom_components.eyeonsaur.helpers.const import ENTRY_LOGIN, ENTRY_PASS


@pytest.mark.asyncio  # AJOUT du marker @pytest.mark.asyncio (même si pas *strictement* nécessaire pour des tests *aussi simples*, *bonne pratique* de le mettre, au cas où 😉)
async def test_first_check_input_valid_email_password() -> None:
    """Test avec email et mot de passe valides."""
    data = {ENTRY_LOGIN: "test@example.com", ENTRY_PASS: "password"}
    errors, exception = await first_check_input(data)
    assert not errors
    assert exception is None


@pytest.mark.asyncio  # AJOUT du marker @pytest.mark.asyncio (bonne pratique)
async def test_first_check_input_invalid_email_format() -> None:
    """Test avec un format d'email invalide."""
    data = {ENTRY_LOGIN: "invalid-email", ENTRY_PASS: "password"}
    errors, exception = await first_check_input(data)
    assert errors == {ENTRY_LOGIN: "invalid_email"}
    assert isinstance(exception, ValueError)


@pytest.mark.asyncio  # AJOUT du marker @pytest.mark.asyncio (bonne pratique)
async def test_first_check_input_missing_password() -> None:
    """Test avec un mot de passe manquant."""
    data = {ENTRY_LOGIN: "test@example.com", ENTRY_PASS: ""}
    errors, exception = await first_check_input(data)
    assert errors == {ENTRY_PASS: "required"}
    assert isinstance(exception, ValueError)


@pytest.mark.asyncio  # AJOUT du marker @pytest.mark.asyncio (bonne pratique)
async def test_first_check_input_missing_email() -> (
    None
):  # MODIF: Nom du test plus précis
    """Test avec un email manquant (champ vide)."""  # MODIF: Description plus précise
    data = {
        ENTRY_LOGIN: "",
        ENTRY_PASS: "password",
    }  # MODIF: Champ ENTRY_LOGIN vide pour simuler un email manquant
    errors, exception = await first_check_input(data)
    assert (
        errors == {ENTRY_LOGIN: "invalid_email"}
    )  # MODIF: Correction assertion: l'erreur attendue pour email vide est 'invalid_email' (et non 'required')
    assert isinstance(
        exception, ValueError
    )  # Vérifie que ValueError est toujours levée
