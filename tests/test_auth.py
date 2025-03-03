import pytest
from saur_client import SaurApiError, SaurClient


async def test_saur_client_authentication_minimal() -> None:
    """Test minimal pour instancier SaurClient et appeler _authenticate()."""
    try:
        client = SaurClient(
            login="dummy_login", password="dummy_password", dev_mode=True
        )  # Paramètres bidon
        await client._authenticate()  # Appel à _authenticate()
    except SaurApiError as e:
        pytest.fail(
            f"Erreur SaurApiError inattendue lors de l'authentification minimale: {e}"
        )
    except Exception as e:
        pytest.fail(
            f"Erreur inattendue lors de l'authentification minimale: {e}"
        )
    else:
        pass  # Si on arrive ici sans exception, le test est un succès
