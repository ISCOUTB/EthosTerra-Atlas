from __future__ import annotations

import pytest
from pathlib import Path

from src.application.simulator_sandbox_service import (
    validate_target_sandbox,
    InstallationSecurityError,
    create_instance_backup,
    rollback_instance
)


def test_sandbox_blocks_writing_to_original_instance(tmp_path):
    orig_root = tmp_path / "EthosTerra_original"
    orig_root.mkdir()
    exp_root = tmp_path / "outputs" / "experiments" / "exp_01" / "EthosTerra_experiment"
    exp_root.mkdir(parents=True)

    target_file = orig_root / "data" / "ebdi" / "goals" / "prepare_land.yaml"

    # Debe levantar InstallationSecurityError
    with pytest.raises(InstallationSecurityError, match="instancia original de solo lectura"):
        validate_target_sandbox(target_file, allowed_experiment_root=exp_root, original_root=orig_root)


def test_sandbox_blocks_writing_outside_experiment_root(tmp_path):
    orig_root = tmp_path / "EthosTerra_original"
    orig_root.mkdir()
    exp_root = tmp_path / "outputs" / "experiments" / "exp_01" / "EthosTerra_experiment"
    exp_root.mkdir(parents=True)

    arbitrary_path = tmp_path / "algun_otro_lugar" / "archivo.yaml"

    with pytest.raises(InstallationSecurityError, match="fuera del sandbox permitido"):
        validate_target_sandbox(arbitrary_path, allowed_experiment_root=exp_root, original_root=orig_root)


def test_sandbox_allows_writing_inside_experiment_root(tmp_path):
    orig_root = tmp_path / "EthosTerra_original"
    orig_root.mkdir()
    exp_root = tmp_path / "outputs" / "experiments" / "exp_01" / "EthosTerra_experiment"
    exp_root.mkdir(parents=True)

    valid_target = exp_root / "data" / "ebdi" / "goals" / "prepare_land.yaml"

    # No debe levantar ninguna excepción
    validate_target_sandbox(valid_target, allowed_experiment_root=exp_root, original_root=orig_root)


def test_backup_and_rollback_mechanism(tmp_path):
    exp_root = tmp_path / "simulator_instance"
    exp_root.mkdir()
    test_file = exp_root / "goal.yaml"
    test_file.write_text("initial: true", encoding="utf-8")

    backup_dir = tmp_path / "backups"

    # 1. Crear backup
    backup_file = create_instance_backup(exp_root, backup_dir, "exp_01")
    assert backup_file.exists()

    # 2. Modificar archivo (simular instalación de nuevo YAML)
    test_file.write_text("initial: false, modified: true", encoding="utf-8")
    assert "modified: true" in test_file.read_text()

    # 3. Ejecutar Rollback
    rollback_instance(backup_file, exp_root)
    assert test_file.exists()
    assert test_file.read_text() == "initial: true"
