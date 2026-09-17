from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

from src.domain.v2.action_catalog_service import ActionCatalogService
from src.application.expression_validator import validate_activation_when


class ArtifactValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    artifact_id: str
    artifact_type: Literal["goal", "plan"]
    file_path: str
    yaml_parseable: bool
    schema_valid: bool
    action_catalog_valid: bool
    plan_ref_resolved: bool
    runtime_compatible: Literal["yes", "no", "unknown"]
    requires_simulation_test: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def validate_goal_yaml(
    file_path: Path,
    artifact_id: str,
    available_plan_ids: set[str]
) -> ArtifactValidationReport:
    errors: list[str] = []
    warnings: list[str] = []

    if not file_path.exists():
        return ArtifactValidationReport(
            artifact_id=artifact_id,
            artifact_type="goal",
            file_path=str(file_path),
            yaml_parseable=False,
            schema_valid=False,
            action_catalog_valid=True,
            plan_ref_resolved=False,
            runtime_compatible="no",
            requires_simulation_test=True,
            errors=[f"Archivo no encontrado: {file_path}"]
        )

    # 1. Parseabilidad YAML
    try:
        content = yaml.safe_load(file_path.read_text(encoding="utf-8"))
        yaml_parseable = True
    except Exception as e:
        return ArtifactValidationReport(
            artifact_id=artifact_id,
            artifact_type="goal",
            file_path=str(file_path),
            yaml_parseable=False,
            schema_valid=False,
            action_catalog_valid=True,
            plan_ref_resolved=False,
            runtime_compatible="no",
            requires_simulation_test=True,
            errors=[f"Error de sintaxis YAML: {e}"]
        )

    if not isinstance(content, dict):
        return ArtifactValidationReport(
            artifact_id=artifact_id,
            artifact_type="goal",
            file_path=str(file_path),
            yaml_parseable=True,
            schema_valid=False,
            action_catalog_valid=True,
            plan_ref_resolved=False,
            runtime_compatible="no",
            requires_simulation_test=True,
            errors=["El contenido del YAML debe ser un diccionario."]
        )

    # 2. Validación de campos obligatorios de GoalSpec
    required_fields = ["id", "version", "pyramid_level", "activation_when", "contribution_rules", "plan_ref"]
    for rf in required_fields:
        if rf not in content:
            errors.append(f"Falta el campo obligatorio de GoalSpec: '{rf}'.")

    # 3. Validación de pirámide
    valid_levels = {"SURVIVAL", "DUTY", "OPPORTUNITY", "NEED", "ATTENTION_CYCLE"}
    if content.get("pyramid_level") not in valid_levels:
        errors.append(f"pyramid_level '{content.get('pyramid_level')}' no es válido. Debe ser uno de {valid_levels}.")

    # 4. Validación de expresión de activación
    activation_expr = content.get("activation_when", "")
    act_res = validate_activation_when(str(activation_expr))
    if not act_res.syntax_valid:
        errors.extend(act_res.syntax_errors)

    # 5. Resolución de plan_ref
    plan_ref = content.get("plan_ref", "")
    plan_ref_resolved = plan_ref in available_plan_ids
    if not plan_ref_resolved:
        errors.append(f"plan_ref '{plan_ref}' no resuelve a ningún PlanSpec disponible en el conjunto.")

    schema_valid = len(errors) == 0

    return ArtifactValidationReport(
        artifact_id=artifact_id,
        artifact_type="goal",
        file_path=str(file_path),
        yaml_parseable=yaml_parseable,
        schema_valid=schema_valid,
        action_catalog_valid=True,
        plan_ref_resolved=plan_ref_resolved,
        runtime_compatible="unknown",
        requires_simulation_test=True,
        errors=errors,
        warnings=warnings
    )


def validate_plan_yaml(
    file_path: Path,
    artifact_id: str
) -> ArtifactValidationReport:
    errors: list[str] = []
    warnings: list[str] = []

    if not file_path.exists():
        return ArtifactValidationReport(
            artifact_id=artifact_id,
            artifact_type="plan",
            file_path=str(file_path),
            yaml_parseable=False,
            schema_valid=False,
            action_catalog_valid=False,
            plan_ref_resolved=True,
            runtime_compatible="no",
            requires_simulation_test=True,
            errors=[f"Archivo no encontrado: {file_path}"]
        )

    try:
        content = yaml.safe_load(file_path.read_text(encoding="utf-8"))
        yaml_parseable = True
    except Exception as e:
        return ArtifactValidationReport(
            artifact_id=artifact_id,
            artifact_type="plan",
            file_path=str(file_path),
            yaml_parseable=False,
            schema_valid=False,
            action_catalog_valid=False,
            plan_ref_resolved=True,
            runtime_compatible="no",
            requires_simulation_test=True,
            errors=[f"Error de sintaxis YAML: {e}"]
        )

    if not isinstance(content, dict):
        return ArtifactValidationReport(
            artifact_id=artifact_id,
            artifact_type="plan",
            file_path=str(file_path),
            yaml_parseable=True,
            schema_valid=False,
            action_catalog_valid=False,
            plan_ref_resolved=True,
            runtime_compatible="no",
            requires_simulation_test=True,
            errors=["El contenido del YAML debe ser un diccionario."]
        )

    required_fields = ["id", "version", "steps"]
    for rf in required_fields:
        if rf not in content:
            errors.append(f"Falta el campo obligatorio de PlanSpec: '{rf}'.")

    steps = content.get("steps", [])
    if not isinstance(steps, list) or len(steps) == 0:
        errors.append("PlanSpec debe tener al menos un paso en 'steps'.")

    action_catalog_valid = True
    for step in steps:
        if not isinstance(step, dict):
            errors.append(f"Paso inválido: {step}")
            action_catalog_valid = False
            continue
        action_name = step.get("action")
        args = step.get("args", {})
        if not action_name:
            errors.append("Paso sin campo 'action'.")
            action_catalog_valid = False
            continue

        ok, step_errors = ActionCatalogService.validate_step(action_name, args)
        if not ok:
            action_catalog_valid = False
            errors.extend(step_errors)

    schema_valid = len(errors) == 0

    return ArtifactValidationReport(
        artifact_id=artifact_id,
        artifact_type="plan",
        file_path=str(file_path),
        yaml_parseable=yaml_parseable,
        schema_valid=schema_valid,
        action_catalog_valid=action_catalog_valid,
        plan_ref_resolved=True,
        runtime_compatible="unknown",
        requires_simulation_test=True,
        errors=errors,
        warnings=warnings
    )
