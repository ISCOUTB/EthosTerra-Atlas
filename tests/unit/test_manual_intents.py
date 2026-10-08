from __future__ import annotations

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.intents_routes import set_intent_service
from src.application.manual_intent_service import (
    ManualIntentService,
    IntentSecurityError,
    IntentNotFoundError,
    IntentAlreadyExistsError,
    IntentRetentionExpiredError,
)
from src.domain.v2.intent_schemas import (
    CreateIntentRequest,
    UpdateIntentRequest,
    validate_identifier,
)
from src.domain.schemas import CasoPuro, CasoConflictivo, FuenteEnColision


def compute_directory_tree_hash(dir_path: Path) -> str:
    """Calcula un hash SHA-256 consolidado y determinista de un árbol de directorios."""
    if not dir_path.exists():
        return "DIR_NOT_FOUND"
    hasher = hashlib.sha256()
    for root, dirs, files in os.walk(dir_path):
        dirs.sort()
        for f in sorted(files):
            file_p = Path(root) / f
            hasher.update(str(file_p.relative_to(dir_path)).encode("utf-8"))
            try:
                hasher.update(file_p.read_bytes())
            except Exception:
                pass
    return hasher.hexdigest()


@pytest.fixture
def isolated_sandbox(tmp_path: Path):
    """Fixture que crea un entorno de prueba aislado con carpetas simuladas."""
    intents_dir = tmp_path / "intents"
    ethos_original = tmp_path / "EthosTerra_original"
    ethos_original.mkdir(parents=True, exist_ok=True)
    # Crear un archivo representativo en EthosTerra_original
    (ethos_original / "core_simulation.py").write_text("# Core simulation code", encoding="utf-8")

    service = ManualIntentService(
        root_dir=intents_dir,
        original_root=ethos_original,
        retention_days=30,
    )
    set_intent_service(service)
    client = TestClient(app)
    return {
        "service": service,
        "client": client,
        "intents_dir": intents_dir,
        "trash_dir": intents_dir / ".trash",
        "ethos_original": ethos_original,
    }


# ==============================================================================
# 1. PRUEBAS DE SEGURIDAD Y VALIDACIÓN DE IDENTIFICADORES
# ==============================================================================

@pytest.mark.parametrize("invalid_id", [
    "../intento_escape",
    "..\\intento_escape",
    "/intento_absoluto",
    "intento/subcarpeta",
    "intento\\subcarpeta",
    "intento\x00nulo",
    " con_espacios_inicio",
    "con_espacios_fin ",
    "con espacios",
    "",
    "a" * 65,  # Excede 64 caracteres
    "intento$especial!",
    "intento.punto",
])
def test_security_invalid_identifiers_rejected(invalid_id: str):
    """Verifica que cualquier identificador no conforme a la lista blanca estricta sea rechazado."""
    with pytest.raises(ValueError):
        validate_identifier(invalid_id)


def test_security_cannot_write_into_ethosterra_original(isolated_sandbox):
    """Verifica que el servicio bloquee categóricamente cualquier intento de ruta en EthosTerra_original."""
    service: ManualIntentService = isolated_sandbox["service"]
    ethos_orig: Path = isolated_sandbox["ethos_original"]

    # Simular un servicio malintencionado configurado en ethos_original
    bad_service = ManualIntentService(
        root_dir=ethos_orig,
        original_root=ethos_orig,
        retention_days=30,
    )
    with pytest.raises(IntentSecurityError):
        bad_service.create_intent(
            CreateIntentRequest(
                id="malicious_intent",
                author="attacker",
                intent=CasoPuro(
                    tipo="puro",
                    clasificacion="ejecutar_accion",
                    confianza=0.9,
                    razonamiento="intento hostil",
                ),
            )
        )


def test_security_symlink_rejected(isolated_sandbox):
    """Verifica el rechazo inmediato de enlaces simbólicos en el destino."""
    service: ManualIntentService = isolated_sandbox["service"]
    intents_dir: Path = isolated_sandbox["intents_dir"]

    # Crear symlink en el directorio
    symlink_target = intents_dir / "target_symlink.json"
    fake_file = isolated_sandbox["ethos_original"] / "core_simulation.py"
    try:
        symlink_target.symlink_to(fake_file)
        with pytest.raises(IntentSecurityError):
            service.get_intent("target_symlink")
    except OSError:
        pytest.skip("El sistema operativo no soporta symlinks en esta ruta.")


def test_ethosterra_original_zero_writes_and_hash_invariance(isolated_sandbox):
    """Verifica que EthosTerra_original permanezca 100% idéntico antes y después de operaciones."""
    ethos_orig: Path = isolated_sandbox["ethos_original"]
    client: TestClient = isolated_sandbox["client"]

    initial_hash = compute_directory_tree_hash(ethos_orig)

    # Realizar operaciones varias mediante API
    client.post(
        "/v2/intents",
        json={
            "id": "intent_pure_test",
            "author": "investigador",
            "intent": {
                "tipo": "puro",
                "clasificacion": "actualizar_creencia",
                "confianza": 0.95,
                "razonamiento": "Verificación de invariante",
            },
        },
    )
    client.delete("/v2/intents/intent_pure_test")
    client.post("/v2/intents/intent_pure_test/restore")

    final_hash = compute_directory_tree_hash(ethos_orig)
    assert initial_hash == final_hash, "Violación crítica: EthosTerra_original fue alterado."


# ==============================================================================
# 2. PRUEBAS CRUD FELICES Y CONFLICTIVAS
# ==============================================================================

def test_crud_happy_path_end_to_end(isolated_sandbox):
    """Flujo feliz completo de creación, lectura, actualización y listado."""
    client: TestClient = isolated_sandbox["client"]
    intents_dir: Path = isolated_sandbox["intents_dir"]

    # 1. Crear Caso Puro
    pure_payload = {
        "id": "intent_001",
        "author": "agronomo_01",
        "intent": {
            "tipo": "puro",
            "clasificacion": "ejecutar_accion",
            "confianza": 0.88,
            "razonamiento": "Suelo óptimo para siembra de maíz.",
        },
    }
    r = client.post("/v2/intents", json=pure_payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["id"] == "intent_001"
    assert data["metadata"]["version"] == 1
    assert data["metadata"]["created_by"] == "agronomo_01"
    assert (intents_dir / "intent_001.json").exists()

    # 2. Leer Caso Puro
    r = client.get("/v2/intents/intent_001")
    assert r.status_code == 200
    assert r.json()["intent"]["clasificacion"] == "ejecutar_accion"

    # 3. Actualizar Caso Puro
    update_payload = {
        "author": "agronomo_02",
        "intent": {
            "tipo": "puro",
            "clasificacion": "consultar_estado",
            "confianza": 0.92,
            "razonamiento": "Se requiere consultar nivel freático antes de sembrar.",
        },
    }
    r = client.put("/v2/intents/intent_001", json=update_payload)
    assert r.status_code == 200
    data = r.json()
    assert data["metadata"]["version"] == 2
    assert data["metadata"]["updated_by"] == "agronomo_02"
    assert data["intent"]["clasificacion"] == "consultar_estado"

    # 4. Crear Caso Conflictivo
    conflict_payload = {
        "id": "intent_conflict_002",
        "author": "revisor_bdi",
        "intent": {
            "tipo": "conflicto",
            "conflicto_detectado": "Conflicto entre ahorro de agua y riego urgente.",
            "opciones_resolucion": [
                "Priorizar conservación de recurso hídrico",
                "Riego por goteo localizado",
            ],
            "requiere_humano": True,
            "fuentes_en_colision": [
                {
                    "source_type": "context_field",
                    "source_id": "water_level_critical",
                    "intencion": "ahorrar_agua",
                    "efecto": "evitar desabastecimiento",
                    "evidence_ref": "sensor_01",
                },
                {
                    "source_type": "document",
                    "source_id": "norma_riego_semanal",
                    "intencion": "regar_parcela",
                    "efecto": "evitar marchitez",
                    "evidence_ref": "manual_normativo_p12",
                },
            ],
        },
    }
    r = client.post("/v2/intents", json=conflict_payload)
    assert r.status_code == 201
    assert r.json()["intent"]["tipo"] == "conflicto"

    # 5. Listar intenciones activas
    r = client.get("/v2/intents")
    assert r.status_code == 200
    intents = r.json()
    assert len(intents) == 2
    ids = [i["id"] for i in intents]
    assert "intent_001" in ids
    assert "intent_conflict_002" in ids


def test_non_overwrite_on_create(isolated_sandbox):
    """Verifica que no se permita sobreescribir un ID existente al crear (HTTP 409)."""
    client: TestClient = isolated_sandbox["client"]

    payload = {
        "id": "duplicate_id",
        "author": "user_a",
        "intent": {
            "tipo": "puro",
            "clasificacion": "ignorar",
            "confianza": 0.5,
            "razonamiento": "Primera creación",
        },
    }
    r = client.post("/v2/intents", json=payload)
    assert r.status_code == 201

    # Intentar crear con el mismo ID
    r = client.post("/v2/intents", json=payload)
    assert r.status_code == 409
    assert "ya existe" in r.json()["detail"]


def test_invalid_schema_does_not_modify_existing(isolated_sandbox):
    """Verifica que una petición inválida de edición sea rechazada sin alterar el archivo previo."""
    client: TestClient = isolated_sandbox["client"]
    intents_dir: Path = isolated_sandbox["intents_dir"]

    # Crear válido
    payload = {
        "id": "immutable_test",
        "author": "user_orig",
        "intent": {
            "tipo": "puro",
            "clasificacion": "ejecutar_accion",
            "confianza": 0.7,
            "razonamiento": "Razonamiento intacto",
        },
    }
    client.post("/v2/intents", json=payload)
    original_bytes = (intents_dir / "immutable_test.json").read_bytes()

    # Intentar actualizar con payload inválido (confianza fuera de rango 0.0-1.0)
    bad_update = {
        "author": "attacker",
        "intent": {
            "tipo": "puro",
            "clasificacion": "ejecutar_accion",
            "confianza": 5.0,  # INVÁLIDO
            "razonamiento": "Mala intención",
        },
    }
    r = client.put("/v2/intents/immutable_test", json=bad_update)
    assert r.status_code == 422

    # Archivo debe estar 100% idéntico
    current_bytes = (intents_dir / "immutable_test.json").read_bytes()
    assert original_bytes == current_bytes


def test_simulated_write_failure_leaves_file_intact(isolated_sandbox):
    """Verifica que un fallo inesperado durante la escritura atómica preserve el archivo previo."""
    service: ManualIntentService = isolated_sandbox["service"]
    intents_dir: Path = isolated_sandbox["intents_dir"]

    # Crear inicial
    req = CreateIntentRequest(
        id="atomic_fail_test",
        author="tester",
        intent=CasoPuro(
            tipo="puro",
            clasificacion="consultar_estado",
            confianza=0.8,
            razonamiento="Inicial",
        ),
    )
    service.create_intent(req)
    original_content = (intents_dir / "atomic_fail_test.json").read_text(encoding="utf-8")

    # Forzar error en os.replace
    with patch("os.replace", side_effect=OSError("Disk write error")):
        with pytest.raises(OSError):
            service.update_intent(
                "atomic_fail_test",
                UpdateIntentRequest(
                    author="tester",
                    intent=CasoPuro(
                        tipo="puro",
                        clasificacion="ejecutar_accion",
                        confianza=0.9,
                        razonamiento="Modificado que debe fallar",
                    ),
                ),
            )

    # El archivo debe conservar su estado previo
    after_content = (intents_dir / "atomic_fail_test.json").read_text(encoding="utf-8")
    assert original_content == after_content
    # Ningún archivo temporal remanente
    temps = list(intents_dir.glob(".tmp_*"))
    assert len(temps) == 0


# ==============================================================================
# 3. PRUEBAS DE BORRADO LÓGICO, RETENCIÓN, RESTAURACIÓN Y PURGA
# ==============================================================================

def test_soft_delete_moves_to_trash_with_metadata(isolated_sandbox):
    """Verifica que eliminar mueva el archivo a .trash/ con metadatos de eliminación."""
    client: TestClient = isolated_sandbox["client"]
    intents_dir: Path = isolated_sandbox["intents_dir"]
    trash_dir: Path = isolated_sandbox["trash_dir"]

    # Crear
    client.post(
        "/v2/intents",
        json={
            "id": "intent_to_delete",
            "author": "creator",
            "intent": {
                "tipo": "puro",
                "clasificacion": "ignorar",
                "confianza": 0.6,
                "razonamiento": "Para eliminar",
            },
        },
    )
    assert (intents_dir / "intent_to_delete.json").exists()

    # Eliminar (borrado lógico)
    r = client.delete("/v2/intents/intent_to_delete?deleted_by=admin_user")
    assert r.status_code == 200
    data = r.json()
    assert data["trash_metadata"]["deleted_by"] == "admin_user"
    assert data["trash_metadata"]["retention_days"] == 30
    assert not (intents_dir / "intent_to_delete.json").exists()
    assert (trash_dir / "intent_to_delete.json").exists()

    # Listar papelera
    r = client.get("/v2/intents/trash")
    assert r.status_code == 200
    trash_items = r.json()
    assert len(trash_items) == 1
    assert trash_items[0]["id"] == "intent_to_delete"
    assert trash_items[0]["trash_metadata"]["is_expired"] is False


def test_restore_within_retention_window(isolated_sandbox):
    """Verifica que restaurar dentro de la ventana de 30 días sea exitoso."""
    client: TestClient = isolated_sandbox["client"]
    intents_dir: Path = isolated_sandbox["intents_dir"]
    trash_dir: Path = isolated_sandbox["trash_dir"]

    # Crear y borrar
    client.post(
        "/v2/intents",
        json={
            "id": "intent_restore_ok",
            "author": "user1",
            "intent": {
                "tipo": "puro",
                "clasificacion": "actualizar_creencia",
                "confianza": 0.85,
                "razonamiento": "Dato para restaurar",
            },
        },
    )
    client.delete("/v2/intents/intent_restore_ok")

    # Restaurar
    r = client.post("/v2/intents/intent_restore_ok/restore", json={"restored_by": "restorer_user"})
    assert r.status_code == 200
    data = r.json()
    assert data["metadata"]["version"] == 2
    assert data["metadata"]["updated_by"] == "restorer_user"
    assert (intents_dir / "intent_restore_ok.json").exists()
    assert not (trash_dir / "intent_restore_ok.json").exists()


def test_restore_expired_intent_fails_with_410_gone(isolated_sandbox):
    """Verifica que restaurar una intención con retención caducada retorne 410 Gone."""
    service: ManualIntentService = isolated_sandbox["service"]
    client: TestClient = isolated_sandbox["client"]
    trash_dir: Path = isolated_sandbox["trash_dir"]

    # Crear y borrar
    client.post(
        "/v2/intents",
        json={
            "id": "intent_expired",
            "author": "user1",
            "intent": {
                "tipo": "puro",
                "clasificacion": "ejecutar_accion",
                "confianza": 0.85,
                "razonamiento": "Caducado",
            },
        },
    )
    client.delete("/v2/intents/intent_expired")

    # Modificar expires_at en el archivo de papelera para simular caducidad
    trash_file = trash_dir / "intent_expired.json"
    data = json.loads(trash_file.read_text(encoding="utf-8"))
    expired_date = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    data["trash_metadata"]["expires_at"] = expired_date
    trash_file.write_text(json.dumps(data), encoding="utf-8")

    # Intentar restaurar
    r = client.post("/v2/intents/intent_expired/restore")
    assert r.status_code == 410
    assert "ha expirado" in r.json()["detail"]


def test_restore_conflict_when_id_reused_returns_409(isolated_sandbox):
    """Verifica que si el ID ya fue recreado en activos, la restauración devuelva 409 Conflict."""
    client: TestClient = isolated_sandbox["client"]

    # Crear y borrar versión 1
    client.post(
        "/v2/intents",
        json={
            "id": "reused_id",
            "author": "user1",
            "intent": {
                "tipo": "puro",
                "clasificacion": "ejecutar_accion",
                "confianza": 0.8,
                "razonamiento": "V1",
            },
        },
    )
    client.delete("/v2/intents/reused_id")

    # Crear una nueva intención activa con el mismo ID
    client.post(
        "/v2/intents",
        json={
            "id": "reused_id",
            "author": "user2",
            "intent": {
                "tipo": "puro",
                "clasificacion": "consultar_estado",
                "confianza": 0.9,
                "razonamiento": "V2 Activa",
            },
        },
    )

    # Intentar restaurar la V1 desde la papelera
    r = client.post("/v2/intents/reused_id/restore")
    assert r.status_code == 409
    assert "ya existe una intención activa" in r.json()["detail"]


def test_purge_removes_only_expired_items(isolated_sandbox):
    """Verifica que la purga elimine únicamente los elementos cuya ventana haya vencido."""
    client: TestClient = isolated_sandbox["client"]
    trash_dir: Path = isolated_sandbox["trash_dir"]

    # 1. Crear item fresco y borrar
    client.post(
        "/v2/intents",
        json={
            "id": "fresh_trash",
            "author": "user",
            "intent": {
                "tipo": "puro",
                "clasificacion": "ignorar",
                "confianza": 0.7,
                "razonamiento": "Fresco",
            },
        },
    )
    client.delete("/v2/intents/fresh_trash")

    # 2. Crear item expirado y borrar
    client.post(
        "/v2/intents",
        json={
            "id": "old_trash",
            "author": "user",
            "intent": {
                "tipo": "puro",
                "clasificacion": "ignorar",
                "confianza": 0.7,
                "razonamiento": "Viejo",
            },
        },
    )
    client.delete("/v2/intents/old_trash")

    # Alterar old_trash para que figure expirado
    old_file = trash_dir / "old_trash.json"
    data = json.loads(old_file.read_text(encoding="utf-8"))
    data["trash_metadata"]["expires_at"] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    old_file.write_text(json.dumps(data), encoding="utf-8")

    # Ejecutar purga bajo demanda
    r = client.post("/v2/intents/trash/purge", json={"purged_by": "test_cleaner"})
    assert r.status_code == 200
    res = r.json()
    assert res["purged_count"] == 1
    assert "old_trash" in res["purged_ids"]

    # Verificar disco
    assert not (trash_dir / "old_trash.json").exists()
    assert (trash_dir / "fresh_trash.json").exists()


def test_audit_log_records_operations(isolated_sandbox):
    """Verifica que cada operación genere un registro append-only estructurado en audit.log."""
    service: ManualIntentService = isolated_sandbox["service"]
    client: TestClient = isolated_sandbox["client"]
    audit_file = service.audit_log_path

    # Crear, actualizar y eliminar
    client.post(
        "/v2/intents",
        json={
            "id": "audited_intent",
            "author": "auditor_user",
            "intent": {
                "tipo": "puro",
                "clasificacion": "ejecutar_accion",
                "confianza": 0.9,
                "razonamiento": "Audit test",
            },
        },
    )
    client.put(
        "/v2/intents/audited_intent",
        json={
            "author": "auditor_user",
            "intent": {
                "tipo": "puro",
                "clasificacion": "consultar_estado",
                "confianza": 0.95,
                "razonamiento": "Audit update",
            },
        },
    )
    client.delete("/v2/intents/audited_intent?deleted_by=auditor_user")

    assert audit_file.exists()
    lines = audit_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 3
    ops = [json.loads(line)["operation"] for line in lines]
    assert "CREATE" in ops
    assert "UPDATE" in ops
    assert "DELETE_SOFT" in ops


def test_human_review_metadata_persistence_and_update(isolated_sandbox):
    """Verifica que el bloque de revisión humana se persista, se actualice y se audite explícitamente."""
    client: TestClient = isolated_sandbox["client"]

    # 1. Crear intención con metadatos de revisión humana explícitos
    create_payload = {
        "id": "intent_with_review_01",
        "author": "agronomo_junior",
        "intent": {
            "tipo": "puro",
            "clasificacion": "ejecutar_accion",
            "confianza": 0.88,
            "razonamiento": "Aplicación de abono orgánico en lote experimental.",
        },
        "human_review": {
            "status": "observado",
            "reviewer": "investigador_pedro",
            "comments": "Requiere ajustar dosis conforme a conductividad eléctrica.",
            "decision_rationale": "Falta evidencia edáfica complementaria en el informe.",
            "requires_additional_review": True,
        },
    }
    r = client.post("/v2/intents", json=create_payload)
    assert r.status_code == 201
    data = r.json()
    assert "human_review" in data
    assert data["human_review"]["status"] == "observado"
    assert data["human_review"]["reviewer"] == "investigador_pedro"
    assert data["human_review"]["comments"] == "Requiere ajustar dosis conforme a conductividad eléctrica."
    assert data["human_review"]["requires_additional_review"] is True
    assert data["human_review"]["reviewed_at"] is not None

    # 2. Consultar por GET y verificar persistencia
    r_get = client.get("/v2/intents/intent_with_review_01")
    assert r_get.status_code == 200
    get_data = r_get.json()
    assert get_data["human_review"]["status"] == "observado"
    assert get_data["human_review"]["decision_rationale"] == "Falta evidencia edáfica complementaria en el informe."

    # 3. Actualizar la revisión a "aprobado"
    update_payload = {
        "author": "investigador_pedro",
        "intent": {
            "tipo": "puro",
            "clasificacion": "ejecutar_accion",
            "confianza": 0.94,
            "razonamiento": "Dosis corregida a 1.5 kg/m2 según conductividad.",
        },
        "human_review": {
            "status": "aprobado",
            "reviewer": "investigador_pedro",
            "comments": "Dosis corregida y verificada con análisis edáfico.",
            "decision_rationale": "Parámetros físico-químicos dentro de umbrales seguros.",
            "requires_additional_review": False,
        },
    }
    r_up = client.put("/v2/intents/intent_with_review_01", json=update_payload)
    assert r_up.status_code == 200
    up_data = r_up.json()
    assert up_data["metadata"]["version"] == 2
    assert up_data["human_review"]["status"] == "aprobado"
    assert up_data["human_review"]["requires_additional_review"] is False
    assert up_data["human_review"]["comments"] == "Dosis corregida y verificada con análisis edáfico."


def test_human_review_backward_compatibility_with_legacy_json(isolated_sandbox):
    """Verifica que archivos JSON antiguos sin human_review se deserialicen con defaults seguros."""
    intents_dir: Path = isolated_sandbox["intents_dir"]
    client: TestClient = isolated_sandbox["client"]

    # Simular un archivo legacy escrito antes de la introducción de human_review
    legacy_file = intents_dir / "legacy_intent_001.json"
    legacy_content = {
        "id": "legacy_intent_001",
        "intent": {
            "tipo": "puro",
            "clasificacion": "observar_entorno",
            "confianza": 0.90,
            "razonamiento": "Caso legado sin metadatos de revisión humana.",
        },
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": "sistema_antiguo",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": "sistema_antiguo",
            "canonical_hash": "legacy_hash_0001",
            "version": 1,
        },
    }
    legacy_file.write_text(json.dumps(legacy_content), encoding="utf-8")

    # Leer vía endpoint
    r = client.get("/v2/intents/legacy_intent_001")
    assert r.status_code == 200
    data = r.json()
    assert "human_review" in data
    assert data["human_review"]["status"] == "pendiente"
    assert data["human_review"]["reviewer"] == "investigador_principal"
    assert data["human_review"]["comments"] == ""
    assert data["human_review"]["requires_additional_review"] is False
