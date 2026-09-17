from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any

from src.domain.v2.operational_schemas import GoalSpecArtifact, PlanSpecArtifact, ArtifactSpecSchema


class IndentedDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def render_goal_yaml(goal: GoalSpecArtifact, document_id: str, approved_hash: str) -> str:
    """Renderiza deterministamente el YAML para un GoalSpec."""
    data: dict[str, Any] = {
        "id": goal.id,
        "version": goal.version,
        "display_name": goal.display_name,
        "description": goal.description,
        "pyramid_level": goal.pyramid_level,
    }
    if goal.sub_level:
        data["sub_level"] = goal.sub_level

    data["plan_ref"] = goal.plan_ref
    data["activation_when"] = goal.activation_when

    cr: dict[str, Any] = {}
    if goal.contribution_rules.fixed_value is not None:
        cr["fixed_value"] = goal.contribution_rules.fixed_value
    if goal.contribution_rules.fuzzy_variable:
        cr["fuzzy_variable"] = goal.contribution_rules.fuzzy_variable
    if goal.contribution_rules.fuzzy_rules:
        cr["rules"] = goal.contribution_rules.fuzzy_rules
    data["contribution_rules"] = cr

    if goal.effects:
        data["effects"] = goal.effects

    if goal.normative_tags:
        data["normative_tags"] = goal.normative_tags

    header = (
        f"# GoalSpec: {goal.id}\n"
        f"# Documento de Origen: {document_id}\n"
        f"# Hash de Aprobación: {approved_hash}\n\n"
    )
    dumped = yaml.dump(data, Dumper=IndentedDumper, sort_keys=False, allow_unicode=True, default_flow_style=False)
    return header + dumped


def render_plan_yaml(plan: PlanSpecArtifact, document_id: str, approved_hash: str) -> str:
    """Renderiza deterministamente el YAML para un PlanSpec."""
    data: dict[str, Any] = {
        "id": plan.id,
        "version": plan.version,
        "description": plan.description,
    }
    if plan.preconditions:
        data["preconditions"] = plan.preconditions

    steps_list = []
    for step in plan.steps:
        s: dict[str, Any] = {
            "id": step.id,
            "action": step.action,
        }
        if step.args:
            s["args"] = step.args
        if step.condition:
            s["condition"] = step.condition
        steps_list.append(s)
    data["steps"] = steps_list

    if plan.on_timeout:
        data["on_timeout"] = [
            {"id": s.id, "action": s.action, "args": s.args} for s in plan.on_timeout
        ]
    else:
        data["on_timeout"] = []

    if plan.on_failure:
        data["on_failure"] = [
            {"id": s.id, "action": s.action, "args": s.args} for s in plan.on_failure
        ]
    else:
        data["on_failure"] = []

    header = (
        f"# PlanSpec: {plan.id}\n"
        f"# Documento de Origen: {document_id}\n"
        f"# Hash de Aprobación: {approved_hash}\n\n"
    )
    dumped = yaml.dump(data, Dumper=IndentedDumper, sort_keys=False, allow_unicode=True, default_flow_style=False)
    return header + dumped


def generate_artifact_yamls(
    artifacts: list[ArtifactSpecSchema],
    output_dir: Path,
    document_id: str,
    approved_hash: str
) -> dict[str, Path]:
    """Genera los archivos YAML en el directorio de salida especificado."""
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files: dict[str, Path] = {}

    for art in artifacts:
        filename = f"{art.content.id}.yaml"
        if art.artifact_type == "goal":
            goals_dir = output_dir / "goals"
            goals_dir.mkdir(parents=True, exist_ok=True)
            target_path = goals_dir / filename
            content_str = render_goal_yaml(art.content, document_id, approved_hash)
        elif art.artifact_type == "plan":
            plans_dir = output_dir / "plans"
            plans_dir.mkdir(parents=True, exist_ok=True)
            target_path = plans_dir / filename
            content_str = render_plan_yaml(art.content, document_id, approved_hash)
        else:
            other_dir = output_dir / "other"
            other_dir.mkdir(parents=True, exist_ok=True)
            target_path = other_dir / filename
            content_str = yaml.dump(art.content.model_dump(mode="json"), sort_keys=False)

        target_path.write_text(content_str, encoding="utf-8")
        generated_files[art.artifact_id] = target_path

    return generated_files
