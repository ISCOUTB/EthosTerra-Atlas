"""Configuración global de fixtures para pruebas de FastAPI y autenticación."""
import pytest
from src.api.main import app
from src.api.auth_routes import get_current_user
from src.domain.auth_schemas import UserProfile


@pytest.fixture(autouse=True)
def override_auth_dependency(request):
    """Sobreescribe automáticamente la dependencia de autenticación para pruebas que no evalúen test_auth.py."""
    if "test_auth" in request.node.nodeid:
        yield
        return

    test_user = UserProfile(
        username="admin_test",
        role="admin",
        display_name="Test Admin",
        is_active=True,
    )
    app.dependency_overrides[get_current_user] = lambda: test_user
    yield
    app.dependency_overrides.pop(get_current_user, None)
