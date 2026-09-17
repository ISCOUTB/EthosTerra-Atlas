from __future__ import annotations

import os
import shutil
import tarfile
from pathlib import Path
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field


class InstallationSecurityError(PermissionError):
    """Excepción lanzada cuando una operación intenta escribir fuera del sandbox o en la instancia original."""
    pass


class SimulatorInstanceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    original_root: Path
    experiment_root: Path
    backup_dir: Path


class InstallationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    experiment_id: str
    installed_files: list[str]
    backup_path: str
    target_instance_root: str
    installed_at: datetime
    rollback_available: bool = True


def validate_target_sandbox(target_path: Path, allowed_experiment_root: Path, original_root: Path) -> None:
    """
    Garantiza que la ruta destino resida estrictamente dentro de EthosTerra_experiment
    y rechaza categóricamente cualquier intento de escribir en EthosTerra_original.
    """
    resolved_target = target_path.resolve()
    resolved_orig = original_root.resolve()
    resolved_exp = allowed_experiment_root.resolve()

    # 1. Prohibición absoluta de escribir en la instancia original
    try:
        resolved_target.relative_to(resolved_orig)
        raise InstallationSecurityError(
            f"Acceso denegado: Intento de escritura en la instancia original de solo lectura: '{resolved_target}'."
        )
    except ValueError:
        # No es subdirectorio de original_root, lo cual es correcto
        pass

    # 2. Confinamiento en el sandbox experimental
    try:
        resolved_target.relative_to(resolved_exp)
    except ValueError:
        raise InstallationSecurityError(
            f"Acceso denegado: La ruta '{resolved_target}' se encuentra fuera del sandbox permitido '{resolved_exp}'."
        )


def create_experimental_copy(original_root: Path, experiment_root: Path) -> dict[str, str]:
    """
    Crea una copia experimental versionada de los subdirectorios declarativos necesarios
    (data/ebdi, besa-python, ethosterra-python, config) sin tocar la instancia original.
    """
    if experiment_root.exists():
        return {"status": "already_exists", "path": str(experiment_root)}

    experiment_root.mkdir(parents=True, exist_ok=True)
    dirs_to_copy = ["data", "config", "besa-python", "ethosterra-python"]

    for d in dirs_to_copy:
        src = original_root / d
        dst = experiment_root / d
        if src.exists():
            shutil.copytree(src, dst, dirs_exist_ok=True)

    return {
        "status": "created",
        "path": str(experiment_root),
        "created_at": datetime.now(timezone.utc).isoformat()
    }


def create_instance_backup(experiment_root: Path, backup_dir: Path, experiment_id: str) -> Path:
    """Genera un archivo de respaldo .tar.gz de la instancia experimental antes de la instalación."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"backup_{experiment_id}_{timestamp}.tar.gz"

    with tarfile.open(backup_file, "w:gz") as tar:
        tar.add(experiment_root, arcname=experiment_root.name)

    return backup_file


def rollback_instance(backup_file: Path, experiment_root: Path) -> None:
    """Restaura la instancia experimental a partir de un respaldo comprimido."""
    if not backup_file.exists():
        raise FileNotFoundError(f"Archivo de respaldo no encontrado: {backup_file}")

    # Limpiar estado alterado
    if experiment_root.exists():
        shutil.rmtree(experiment_root)

    parent_dir = experiment_root.parent
    with tarfile.open(backup_file, "r:gz") as tar:
        tar.extractall(path=parent_dir)
