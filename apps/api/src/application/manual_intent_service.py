from __future__ import annotations

import os
import json
import uuid
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Any

from src.domain.v2.intent_schemas import (
    validate_identifier,
    IntentPayload,
    CreateIntentRequest,
    UpdateIntentRequest,
    IntentResponse,
    IntentMetadata,
    TrashMetadata,
    TrashIntentResponse,
    PurgeResponse,
)
from src.application.simulator_sandbox_service import InstallationSecurityError


class IntentSecurityError(PermissionError):
    """Excepción para violaciones de confinamiento o ruta prohibida."""
    pass


class IntentNotFoundError(FileNotFoundError):
    """Excepción cuando el intento no existe en el almacén activo o papelera."""
    pass


class IntentAlreadyExistsError(FileExistsError):
    """Excepción cuando el intento ya existe al intentar crear o restaurar."""
    pass


class IntentRetentionExpiredError(Exception):
    """Excepción cuando el periodo de retención en papelera ha caducado (HTTP 410)."""
    pass


def compute_intent_hash(payload: dict[str, Any]) -> str:
    """Calcula hash determinista SHA-256 sobre payload JSON ordenado y normalizado."""
    canonical_str = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


class ManualIntentService:
    """
    Servicio de aplicación para el ciclo de vida manual de intenciones eBDI (B5).
    Garantiza aislamiento estricto, escrituras atómicas, borrado lógico de 30 días,
    auditoría canónica y protección absoluta contra escrituras fuera del sandbox.
    """

    def __init__(
        self,
        root_dir: Path | None = None,
        original_root: Path | None = None,
        retention_days: int = 30,
    ):
        if root_dir is None:
            # Buscar raíz del proyecto
            current = Path(__file__).resolve()
            project_root = current.parents[min(3, len(current.parents) - 1)]
            for parent in current.parents:
                if (parent / "evals").exists() or (parent / "contracts").exists() or (parent / ".git").exists():
                    project_root = parent
                    break
            root_dir = project_root / "outputs" / "intents"

        self.root_dir = root_dir.resolve()
        self.trash_dir = (self.root_dir / ".trash").resolve()
        self.audit_log_path = self.root_dir / "audit.log"
        self.retention_days = int(os.environ.get("INTENT_RETENTION_DAYS", retention_days))

        if original_root is None:
            self.original_root = Path(
                os.environ.get(
                    "ORIGINAL_ETHOS_ROOT",
                    "/Volumes/ADATA SD620/Programacion 7.0/universidad/proyecto de grado/EthosTerra",
                )
            ).resolve()
        else:
            self.original_root = original_root.resolve()

        # Asegurar directorios de almacenamiento y papelera
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.trash_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_and_validate_path(self, intent_id: str, is_trash: bool = False) -> Path:
        """
        Valida el ID contra la lista blanca estricta y comprueba que la ruta destino
        esté estrictamente confinada en el directorio autorizado sin symlinks.
        """
        clean_id = validate_identifier(intent_id)
        base_dir = self.trash_dir if is_trash else self.root_dir
        target_path = (base_dir / f"{clean_id}.json").resolve()

        # 1. Prohibición absoluta de tocar EthosTerra_original
        try:
            target_path.relative_to(self.original_root)
            raise IntentSecurityError(
                f"Acceso denegado: Intento de ruta dentro de la instancia original protegida '{self.original_root}'."
            )
        except ValueError:
            pass

        # 2. Confinamiento dentro del directorio base autorizado
        try:
            target_path.relative_to(base_dir)
        except ValueError:
            raise IntentSecurityError(
                f"Acceso denegado: La ruta '{target_path}' no reside en el directorio permitido '{base_dir}'."
            )

        # 3. Rechazo categórico de symlinks
        if target_path.is_symlink():
            raise IntentSecurityError(f"Acceso denegado: La ruta destino '{target_path}' es un enlace simbólico.")

        return target_path

    def _log_audit(
        self,
        operation: str,
        intent_id: str,
        user: str,
        canonical_hash: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Registra la operación en el archivo de auditoría append-only."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "intent_id": intent_id,
            "user": user,
            "canonical_hash": canonical_hash,
            "details": details or {},
        }
        line = json.dumps(entry, ensure_ascii=False) + "\n"
        with open(self.audit_log_path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())

    def _atomic_write_json(self, target_path: Path, data: dict[str, Any]) -> None:
        """
        Escritura atómica garantizada:
        1. Escribe a un archivo temporal único en el mismo directorio.
        2. Realiza flush() y fsync() al descriptor del archivo.
        3. Realiza os.replace() atómico hacia el destino.
        4. Si ocurre cualquier error, elimina el temporal y deja intacto el archivo previo.
        """
        parent_dir = target_path.parent
        temp_path = parent_dir / f".tmp_{target_path.name}_{uuid.uuid4().hex}"
        try:
            content_str = json.dumps(data, indent=2, ensure_ascii=False)
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content_str)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, target_path)
        except Exception:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise

    # --------------------------------------------------------------------------
    # OPERACIONES CRUD
    # --------------------------------------------------------------------------

    def create_intent(self, req: CreateIntentRequest) -> IntentResponse:
        """Crea una nueva intención manual asegurando no-sobreescritura."""
        target_path = self._resolve_and_validate_path(req.id)
        if target_path.exists():
            raise IntentAlreadyExistsError(f"La intención con id '{req.id}' ya existe.")

        now = datetime.now(timezone.utc)
        payload_dict = req.intent.model_dump(mode="json")
        chash = compute_intent_hash(payload_dict)

        metadata = IntentMetadata(
            created_at=now,
            created_by=req.author,
            updated_at=now,
            updated_by=req.author,
            canonical_hash=chash,
            version=1,
        )

        response_obj = IntentResponse(
            id=req.id,
            intent=req.intent,
            metadata=metadata,
        )

        record_data = response_obj.model_dump(mode="json")
        self._atomic_write_json(target_path, record_data)
        self._log_audit(
            operation="CREATE",
            intent_id=req.id,
            user=req.author,
            canonical_hash=chash,
            details={"tipo": req.intent.tipo},
        )
        return response_obj

    def get_intent(self, intent_id: str) -> IntentResponse:
        """Lee una intención activa por su identificador."""
        target_path = self._resolve_and_validate_path(intent_id)
        if not target_path.exists() or not target_path.is_file():
            raise IntentNotFoundError(f"Intención '{intent_id}' no encontrada en almacén activo.")

        with open(target_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return IntentResponse.model_validate(raw)

    def list_intents(self) -> list[IntentResponse]:
        """Lista todas las intenciones activas ordenadas alfabéticamente por id."""
        results: list[IntentResponse] = []
        for file_path in sorted(self.root_dir.glob("*.json")):
            if file_path.is_file() and not file_path.name.startswith("."):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                    results.append(IntentResponse.model_validate(raw))
                except Exception:
                    # Ignorar archivos corruptos o no conformes en listado
                    continue
        return results

    def update_intent(self, intent_id: str, req: UpdateIntentRequest) -> IntentResponse:
        """
        Actualiza una intención existente.
        Valida primero con el esquema; si la validación falla, el archivo no se toca.
        """
        target_path = self._resolve_and_validate_path(intent_id)
        if not target_path.exists() or not target_path.is_file():
            raise IntentNotFoundError(f"Intención '{intent_id}' no encontrada para actualizar.")

        # Leer archivo existente para conservar metadatos históricos
        with open(target_path, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
        existing_obj = IntentResponse.model_validate(existing_data)

        now = datetime.now(timezone.utc)
        payload_dict = req.intent.model_dump(mode="json")
        chash = compute_intent_hash(payload_dict)

        new_metadata = IntentMetadata(
            created_at=existing_obj.metadata.created_at,
            created_by=existing_obj.metadata.created_by,
            updated_at=now,
            updated_by=req.author,
            canonical_hash=chash,
            version=existing_obj.metadata.version + 1,
        )

        updated_obj = IntentResponse(
            id=intent_id,
            intent=req.intent,
            metadata=new_metadata,
        )

        record_data = updated_obj.model_dump(mode="json")
        self._atomic_write_json(target_path, record_data)
        self._log_audit(
            operation="UPDATE",
            intent_id=intent_id,
            user=req.author,
            canonical_hash=chash,
            details={"version": new_metadata.version, "tipo": req.intent.tipo},
        )
        return updated_obj

    # --------------------------------------------------------------------------
    # BORRADO LÓGICO, RESTAURACIÓN Y PURGA
    # --------------------------------------------------------------------------

    def delete_intent(self, intent_id: str, deleted_by: str = "operador_manual") -> TrashIntentResponse:
        """
        Borrado lógico: Mueve el archivo a la papelera .trash/ con metadatos de eliminación
        y ventana de retención (30 días por defecto). El archivo activo se desvincula.
        """
        active_path = self._resolve_and_validate_path(intent_id, is_trash=False)
        if not active_path.exists() or not active_path.is_file():
            raise IntentNotFoundError(f"Intención '{intent_id}' no encontrada para eliminar.")

        with open(active_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        active_obj = IntentResponse.model_validate(raw)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=self.retention_days)

        trash_meta = TrashMetadata(
            deleted_at=now,
            deleted_by=deleted_by,
            retention_days=self.retention_days,
            expires_at=expires_at,
            is_expired=False,
        )

        trash_obj = TrashIntentResponse(
            id=active_obj.id,
            intent=active_obj.intent,
            metadata=active_obj.metadata,
            trash_metadata=trash_meta,
        )

        trash_path = self._resolve_and_validate_path(intent_id, is_trash=True)
        # Escritura atómica en papelera
        self._atomic_write_json(trash_path, trash_obj.model_dump(mode="json"))
        # Desvincular de activos
        active_path.unlink()

        self._log_audit(
            operation="DELETE_SOFT",
            intent_id=intent_id,
            user=deleted_by,
            canonical_hash=active_obj.metadata.canonical_hash,
            details={"retention_days": self.retention_days, "expires_at": expires_at.isoformat()},
        )
        return trash_obj

    def list_trash(self) -> list[TrashIntentResponse]:
        """Lista las intenciones en la papelera indicando si han expirado."""
        results: list[TrashIntentResponse] = []
        now = datetime.now(timezone.utc)
        for file_path in sorted(self.trash_dir.glob("*.json")):
            if file_path.is_file() and not file_path.name.startswith("."):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                    obj = TrashIntentResponse.model_validate(raw)
                    # Actualizar estado de expiración dinámicamente
                    obj.trash_metadata.is_expired = now > obj.trash_metadata.expires_at
                    results.append(obj)
                except Exception:
                    continue
        return results

    def restore_intent(self, intent_id: str, restored_by: str = "operador_manual") -> IntentResponse:
        """
        Restaura un intento desde la papelera.
        Reglas:
        - Si no está en papelera -> 404 (IntentNotFoundError).
        - Si expiró la retención (> 30 días) -> 410 (IntentRetentionExpiredError).
        - Si el ID ya fue reutilizado por una intención activa -> 409 (IntentAlreadyExistsError).
        """
        trash_path = self._resolve_and_validate_path(intent_id, is_trash=True)
        if not trash_path.exists() or not trash_path.is_file():
            raise IntentNotFoundError(f"Intención '{intent_id}' no encontrada en la papelera.")

        with open(trash_path, "r", encoding="utf-8") as f:
            trash_data = json.load(f)
        trash_obj = TrashIntentResponse.model_validate(trash_data)

        now = datetime.now(timezone.utc)
        if now > trash_obj.trash_metadata.expires_at:
            raise IntentRetentionExpiredError(
                f"El periodo de retención ({trash_obj.trash_metadata.retention_days} días) para '{intent_id}' ha expirado el {trash_obj.trash_metadata.expires_at.isoformat()}."
            )

        active_path = self._resolve_and_validate_path(intent_id, is_trash=False)
        if active_path.exists():
            raise IntentAlreadyExistsError(
                f"Conflicto de restauración: ya existe una intención activa con id '{intent_id}'."
            )

        # Metadatos actualizados de restauración
        new_metadata = IntentMetadata(
            created_at=trash_obj.metadata.created_at,
            created_by=trash_obj.metadata.created_by,
            updated_at=now,
            updated_by=restored_by,
            canonical_hash=trash_obj.metadata.canonical_hash,
            version=trash_obj.metadata.version + 1,
        )

        restored_obj = IntentResponse(
            id=trash_obj.id,
            intent=trash_obj.intent,
            metadata=new_metadata,
        )

        # Escribir atómicamente a activo y eliminar de papelera
        self._atomic_write_json(active_path, restored_obj.model_dump(mode="json"))
        trash_path.unlink()

        self._log_audit(
            operation="RESTORE",
            intent_id=intent_id,
            user=restored_by,
            canonical_hash=trash_obj.metadata.canonical_hash,
            details={"previous_version": trash_obj.metadata.version},
        )
        return restored_obj

    def purge_trash(self, purged_by: str = "system") -> PurgeResponse:
        """
        Purga definitiva: Elimina de forma irrecuperable exclusivamente los archivos
        en papelera que hayan superado la ventana de retención. Se registra en auditoría.
        """
        purged_ids: list[str] = []
        now = datetime.now(timezone.utc)

        for file_path in list(self.trash_dir.glob("*.json")):
            if file_path.is_file() and not file_path.name.startswith("."):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                    trash_obj = TrashIntentResponse.model_validate(raw)
                    if now > trash_obj.trash_metadata.expires_at:
                        file_path.unlink()
                        purged_ids.append(trash_obj.id)
                        self._log_audit(
                            operation="PURGE_EXPIRED",
                            intent_id=trash_obj.id,
                            user=purged_by,
                            canonical_hash=trash_obj.metadata.canonical_hash,
                            details={"expired_at": trash_obj.trash_metadata.expires_at.isoformat()},
                        )
                except Exception:
                    continue

        return PurgeResponse(
            purged_count=len(purged_ids),
            purged_ids=purged_ids,
            timestamp=now,
            triggered_by=purged_by,
        )
