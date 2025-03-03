"""Tests unitaires pour la fonction first_check_input du config flow."""

from custom_components.eyeonsaur.config_flow import first_check_input
from custom_components.eyeonsaur.helpers.const import ENTRY_LOGIN, ENTRY_PASS


async def test_first_check_input_valid_email_password() -> None:
    """Test avec email et mot de passe valides."""
    data = {ENTRY_LOGIN: "test@example.com", ENTRY_PASS: "password"}
    errors, exception = await first_check_input(data)
    assert not errors
    assert exception is None


async def test_first_check_input_invalid_email_format() -> None:
    """Test avec un format d'email invalide."""
    data = {ENTRY_LOGIN: "invalid-email", ENTRY_PASS: "password"}
    errors, exception = await first_check_input(data)
    assert errors == {ENTRY_LOGIN: "invalid_email"}
    assert isinstance(exception, ValueError)


async def test_first_check_input_missing_password() -> None:
    """Test avec un mot de passe manquant."""
    data = {ENTRY_LOGIN: "test@example.com", ENTRY_PASS: ""}
    errors, exception = await first_check_input(data)
    assert errors == {ENTRY_PASS: "required"}
    assert isinstance(exception, ValueError)


async def test_first_check_input_missing_email() -> None:
    """Test avec un email manquant."""
    data = {ENTRY_LOGIN: "", ENTRY_PASS: "password"}
    errors, exception = await first_check_input(data)
    assert errors == {
        ENTRY_LOGIN: "invalid_email"
    }  # TODO: Vérifier l'erreur exacte retournée dans ce cas
    assert isinstance(
        exception, ValueError
    )  # TODO: Vérifier l'exception exacte retournée dans ce cas
