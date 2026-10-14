"""Pruebas unitarias de seguridad y autenticación soberana (PBKDF2, JWT y anti-inyección)."""
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from src.api.main import app
from src.domain.auth_schemas import LoginRequest, UserProfile
from src.application.auth_service import AuthService
from src.api.auth_routes import get_current_user


@pytest.fixture
def auth_service_tmp(tmp_path):
    """Instancia aislada de AuthService sobre directorio temporal."""
    return AuthService(storage_dir=tmp_path / "auth")


def test_pbkdf2_hashing_and_timing_attack_resistance(auth_service_tmp):
    """El servicio debe generar hashes únicos con salt y verificar en tiempo constante."""
    salt1, hash1 = auth_service_tmp.hash_password("SuperSecret123!")
    salt2, hash2 = auth_service_tmp.hash_password("SuperSecret123!")

    # Salts aleatorios de 16 bytes deben ser distintos para la misma contraseña
    assert salt1 != salt2
    assert hash1 != hash2

    # Verificación válida
    assert auth_service_tmp.verify_password("SuperSecret123!", salt1, hash1) is True
    # Verificación inválida
    assert auth_service_tmp.verify_password("WrongPassword!", salt1, hash1) is False
    assert auth_service_tmp.verify_password("SuperSecret123!", salt2, hash1) is False


def test_username_regex_blocks_sqli_and_path_traversal():
    """El validador Pydantic V2 debe rechazar payloads de SQLi y Path Traversal en username."""
    # Válidos
    assert LoginRequest(username="admin", password="password123").username == "admin"
    assert LoginRequest(username="juan_perez-2026", password="password123").username == "juan_perez-2026"
    assert LoginRequest(username="curador.montes", password="password123").username == "curador.montes"

    # Inyección SQL
    with pytest.raises(ValidationError):
        LoginRequest(username="' OR '1'='1", password="password123")

    with pytest.raises(ValidationError):
        LoginRequest(username="admin; DROP TABLE users;--", password="password123")

    # Path Traversal
    with pytest.raises(ValidationError):
        LoginRequest(username="../../etc/passwd", password="password123")

    # Espacios y caracteres no permitidos
    with pytest.raises(ValidationError):
        LoginRequest(username="admin user", password="password123")

    with pytest.raises(ValidationError):
        LoginRequest(username="ad", password="password123")  # Menos de 3 caracteres


def test_jwt_token_creation_and_tampering_detection(auth_service_tmp):
    """Un token JWT manipulado o firmado con clave incorrecta debe ser rechazado."""
    profile = UserProfile(
        username="admin",
        role="admin",
        display_name="Admin Test",
        is_active=True,
    )
    token = auth_service_tmp.create_access_token(profile, expires_delta=3600)
    assert isinstance(token, str)
    assert token.count(".") == 2

    # Verificación de token legítimo
    verified = auth_service_tmp.verify_token(token)
    assert verified is not None
    assert verified.username == "admin"
    assert verified.role == "admin"

    # Token manipulado en el payload (intento de elevar privilegios)
    parts = token.split(".")
    tampered_token = f"{parts[0]}.eyJyZXN0cmljdGVkIjpmYWxzZX0.{parts[2]}"
    assert auth_service_tmp.verify_token(tampered_token) is None

    # Token expirado (exp = tiempo pasado)
    expired_token = auth_service_tmp.create_access_token(profile, expires_delta=-10)
    assert auth_service_tmp.verify_token(expired_token) is None


def test_http_endpoint_login_flow():
    """El endpoint /v2/auth/login debe autenticar y responder JWT válido."""
    client = TestClient(app)

    # 1. Credenciales inválidas
    bad_res = client.post("/v2/auth/login", json={"username": "admin", "password": "WrongPassword!"})
    assert bad_res.status_code == 401
    assert "inválidas" in bad_res.json()["detail"].lower()

    # 2. Credenciales correctas del admin inicial por defecto
    good_res = client.post("/v2/auth/login", json={"username": "admin", "password": "EthosTerra2026!"})
    assert good_res.status_code == 200
    data = good_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "admin"

    # 3. Consultar /v2/auth/me con el token obtenido
    token = data["access_token"]
    me_res = client.get("/v2/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "admin"

    # 4. Consultar /v2/auth/me sin token -> 401
    unauth_res = client.get("/v2/auth/me")
    assert unauth_res.status_code == 401


def test_atlas_context_review_authenticated_vs_unauthenticated(tmp_path, monkeypatch):
    """Verifica que el usuario autenticado con Bearer token registre su perfil en vez de anónimo."""
    from apps.atlas.storage.manifest_manager import ManifestManager
    from apps.atlas.schemas.document_schemas import DocumentMetadataRecord, AtlasManifestState

    client = TestClient(app)

    # 1. Preparar un manifiesto con un documento de prueba
    manifest_mgr = ManifestManager(base_dir=tmp_path / "quarantine")
    manifest_mgr.ensure_directories()
    test_doc = DocumentMetadataRecord(
        source_id="doc_test_auth",
        entity="alcaldia_el_carmen",
        title="Documento de Prueba Auth",
        level="municipal",
        territory_scope="13244",
        pipeline_type="documental",
        document_format="pdf",
        canonical_url="local_upload://doc_test_auth.pdf",
        download_date="2026-10-14T00:00:00Z",
        sha256="0" * 64,
        byte_size=1024,
        content_path="sources/000.pdf",
        source_type="document_context",
        provenance_class="official_government",
        consent_status="not_applicable",
        allowed_for_training=False,
        usage_state="context_only",
        approval_status="pending_context_review",
        status="pending_context_review",
    )
    manifest = AtlasManifestState(last_updated="2026-10-14T00:00:00Z", documents={"doc_test_auth": test_doc})
    manifest_mgr.save_manifest(manifest)

    # Mockear manifest_manager en el módulo de rutas activo
    import src.api.atlas_routes as atlas_routes_module
    monkeypatch.setattr(atlas_routes_module, "manifest_manager", manifest_mgr)

    # A) Revisión SIN token: modo 'declarado_sin_autenticacion'
    res_anon = client.post(
        "/v2/atlas/artifacts/context-review",
        json={
            "source_id": "doc_test_auth",
            "decision": "approved_for_context",
            "review_notes": "Aprobación anónima declarada",
            "reviewer_id": "curador_anonimo",
        },
    )
    assert res_anon.status_code == 200
    doc_anon = res_anon.json()
    assert doc_anon["reviewer_auth_mode"] == "declarado_sin_autenticacion"
    assert doc_anon["reviewer_id"] == "curador_anonimo"

    # B) Revisión CON token Bearer: modo 'bearer_jwt_authenticated' con perfil real
    login_res = client.post("/v2/auth/login", json={"username": "admin", "password": "EthosTerra2026!"})
    token = login_res.json()["access_token"]

    res_auth = client.post(
        "/v2/atlas/artifacts/context-review",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "source_id": "doc_test_auth",
            "decision": "approved_for_context",
            "review_notes": "Aprobación soberana autenticada con JWT",
            "reviewer_id": "nombre_no_relevante_porque_se_sobrescribe_con_perfil",
        },
    )
    assert res_auth.status_code == 200
    doc_auth = res_auth.json()
    assert doc_auth["reviewer_auth_mode"] == "bearer_jwt_authenticated"
    assert doc_auth["reviewer_id"] == "admin"

