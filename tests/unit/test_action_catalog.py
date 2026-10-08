from __future__ import annotations

import pytest
from src.domain.v2.action_catalog_service import ActionCatalogService


def test_action_catalog_loads_successfully():
    catalog = ActionCatalogService.load_catalog()
    assert "catalog_version" in catalog
    assert "provenance" in catalog
    assert "actions" in catalog
    count = ActionCatalogService.get_action_count()
    assert count > 0


def test_validate_step_valid_agro_operation():
    ok, errors = ActionCatalogService.validate_step(
        "agro_ecosystem_operation",
        {"operation": "PREPARE"}
    )
    assert ok is True
    assert len(errors) == 0


def test_validate_step_invalid_operation_value():
    ok, errors = ActionCatalogService.validate_step(
        "agro_ecosystem_operation",
        {"operation": "FUMIGAR_ILEGAL"}
    )
    assert ok is False
    assert any("no es válido" in e for e in errors)


def test_validate_step_missing_required_arg():
    ok, errors = ActionCatalogService.validate_step(
        "agro_ecosystem_operation",
        {}  # Falta 'operation'
    )
    assert ok is False
    assert any("requiere el argumento obligatorio 'operation'" in e for e in errors)


def test_validate_step_extra_disallowed_arg():
    ok, errors = ActionCatalogService.validate_step(
        "agro_ecosystem_operation",
        {"operation": "PREPARE", "parametro_inventado": 123}
    )
    assert ok is False
    assert any("no permite el argumento no reconocido" in e for e in errors)


def test_validate_step_nonexistent_action():
    ok, errors = ActionCatalogService.validate_step(
        "accion_inexistente_xyz",
        {"arg": 1}
    )
    assert ok is False
    assert any("no existe en el catálogo" in e for e in errors)


def test_validate_emit_episode_valid():
    ok, errors = ActionCatalogService.validate_step(
        "emit_episode",
        {"text": "Trabajé en la preparación del terreno.", "tags": ["agro", "prepare"]}
    )
    assert ok is True
    assert len(errors) == 0


def test_action_catalog_format_summary_for_prompt():
    summary = ActionCatalogService.format_catalog_summary_for_prompt()
    assert "CATÁLOGO DE ACCIONES VÁLIDAS DE ETHOSTERRA" in summary
    assert "agro_ecosystem_operation" in summary
    assert "send_marketplace_event" in summary


def test_action_catalog_list_available_and_reset():
    catalogs = ActionCatalogService.list_available_catalogs()
    assert "actions_catalog_v1.json" in catalogs
    current_path = ActionCatalogService.get_catalog_path()
    assert current_path.name == "actions_catalog_v1.json"
    ActionCatalogService.reset_catalog()
    assert ActionCatalogService.get_catalog_path().name == "actions_catalog_v1.json"
