from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import jsonschema

from apps.atlas.schemas.context_schemas import TerritorialBeliefItem
from src.domain.v2.action_catalog_service import ActionCatalogService
from src.domain.v2.operational_schemas import (
    ContributionRulesSchema,
    GoalSpecArtifact,
    PlanSpecArtifact,
    StepSpecSchema,
)
from src.application.yaml_generator import render_goal_yaml, render_plan_yaml

logger = logging.getLogger("ebdi_yaml_compiler")


class CompilationError(Exception):
    """Error en la compilación declarativa de creencias a YAML de simulación."""


def _safe_relpath(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def _sanitize_snake_id(raw: str, default_prefix: str = "item") -> str:
    """Asegura que el identificador cumpla rigurosamente con ^[a-z][a-z0-9_]*$."""
    clean = re.sub(r"[^a-zA-Z0-9_]+", "_", raw).strip("_").lower()
    clean = re.sub(r"_+", "_", clean)
    if not clean or not clean[0].isalpha():
        clean = f"{default_prefix}_{clean}"
    return clean[:48]


def _map_pillar_to_pyramid(pillar: str) -> tuple[str, str]:
    """Mapea el pilar territorial al nivel de la pirámide de deseos y subnivel en EthosTerra."""
    p = pillar.lower()
    if "ambiente" in p or "agua" in p or "clima" in p:
        return "SURVIVAL", "L1_SURVIVAL"
    if "tierra" in p or "propiedad" in p or "ordenamiento" in p:
        return "DUTY", "L2_OBLIGATION"
    if "infraestructura" in p or "vial" in p or "maquinaria" in p:
        return "NEED", "L4_SKILLS_AND_RESOURCES"
    if "comunitari" in p or "social" in p or "asociat" in p:
        return "DUTY", "L5_SOCIAL"
    # Por defecto para reactivación económica agropecuaria
    return "OPPORTUNITY", "L3_PRODUCTIVE_DEVELOPMENT"


def _build_action_args(belief: TerritorialBeliefItem) -> dict[str, Any]:
    """Construye argumentos válidos para la acción según el catálogo de EthosTerra."""
    actions = ActionCatalogService.get_actions()
    action_name = belief.executable_action
    spec = actions.get(action_name, {})
    arg_specs = spec.get("arg_specs", {})
    args: dict[str, Any] = {}

    if action_name == "agro_ecosystem_operation":
        op = belief.action_operation_type or "PREPARE"
        allowed_ops = arg_specs.get("operation", {}).get("allowed_values", ["PREPARE"])
        if op not in allowed_ops:
            op = "PREPARE"
        args["operation"] = op

    elif action_name == "send_marketplace_event":
        sub_op = belief.action_operation_type or "BUY_SEEDS"
        allowed_types = arg_specs.get("message_type", {}).get("allowed_values", ["BUY_SEEDS"])
        if sub_op not in allowed_types:
            sub_op = "BUY_SEEDS"
        args["message_type"] = sub_op
        args["quantity"] = 1
        args["reset_resource_needed"] = True

    elif action_name == "send_society_collaboration":
        args["flag"] = "community_aid"
        args["amount"] = 5
        args["guard"] = "offer"

    elif action_name == "consume_resource":
        args["key"] = "water_available"
        args["amount"] = 1.0

    elif action_name == "increment_belief":
        key = _sanitize_snake_id(belief.belief_key, "var")
        args["key"] = key
        args["amount"] = 1.0

    elif action_name == "update_belief":
        key = _sanitize_snake_id(belief.belief_key, "var")
        args["key"] = key
        args["value"] = True

    elif action_name == "emit_emotion":
        args["axis"] = "hopeful"
        args["delta"] = 0.05

    elif action_name == "spend_friends_time":
        args["happiness_gain"] = 0.05

    return args


class EBDIYamlCompiler:
    """Compilador determinista de Creencias Territoriales a especificaciones GoalSpec y PlanSpec en YAML."""

    def __init__(self, schemas_dir: Path | None = None, output_base_dir: Path | None = None):
        self.output_base_dir = (output_base_dir or Path("outputs/atlas/yaml")).resolve()
        self.goals_dir = self.output_base_dir / "goals"
        self.plans_dir = self.output_base_dir / "plans"
        self.goals_dir.mkdir(parents=True, exist_ok=True)
        self.plans_dir.mkdir(parents=True, exist_ok=True)

        # Esquemas oficiales para validación
        self.schemas_dir = (
            schemas_dir
            or Path("outputs/experiments/exp_vertical_001/EthosTerra_experiment/data/ebdi/schemas")
        ).resolve()
        self.goal_schema = self._load_schema("GoalSpec.schema.json")
        self.plan_schema = self._load_schema("PlanSpec.schema.json")

    def _load_schema(self, schema_filename: str) -> dict[str, Any] | None:
        schema_path = self.schemas_dir / schema_filename
        if schema_path.is_file():
            try:
                with open(schema_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"No se pudo cargar esquema {schema_filename}: {e}")
        return None

    def compile_belief_to_artifacts(
        self,
        belief: TerritorialBeliefItem,
        document_id: str,
        document_hash: str,
    ) -> tuple[GoalSpecArtifact, PlanSpecArtifact]:
        """Transforma una creencia curada en las instancias formales de GoalSpec y PlanSpec."""
        clean_key = _sanitize_snake_id(belief.belief_key, "territorial")
        goal_id = f"{clean_key}_goal_v1"
        plan_id = f"{clean_key}_plan_v1"

        pyramid_level, sub_level = _map_pillar_to_pyramid(belief.pillar)

        # 1. Construir MVEL de activación
        activation_when = belief.activation_rule_template.strip()
        if not activation_when or len(activation_when) < 3:
            activation_when = f"belief.get('{clean_key}') == true"

        # 2. Reglas de contribución difusa / valor fijo
        conf = max(0.1, min(1.0, float(belief.confidence)))
        contribution_rules = ContributionRulesSchema(fixed_value=round(conf, 2))

        # 3. Normative tags
        normative_tags = [
            f"source_{_sanitize_snake_id(belief.source_id)}",
            f"pillar_{_sanitize_snake_id(belief.pillar)}",
        ]
        for muni in belief.target_municipalities:
            normative_tags.append(f"muni_{_sanitize_snake_id(muni)}")

        goal = GoalSpecArtifact(
            id=goal_id,
            version="1.0",
            display_name=belief.topic[:100],
            description=belief.ebdi_belief_assertion[:300],
            pyramid_level=pyramid_level,  # type: ignore
            sub_level=sub_level,  # type: ignore
            activation_when=activation_when,
            contribution_rules=contribution_rules,
            plan_ref=plan_id,
            normative_tags=normative_tags,
        )

        # 4. Pasos del Plan
        primary_args = _build_action_args(belief)
        step_1 = StepSpecSchema(
            id=f"{_sanitize_snake_id(belief.executable_action, 'step')}_op",
            action=belief.executable_action,
            args=primary_args,
        )

        bio_text = belief.behavioral_effect or belief.ebdi_belief_assertion
        step_2 = StepSpecSchema(
            id="emit_territorial_episode",
            action="emit_episode",
            args={
                "text": bio_text[:190],
                "tags": ["territorial_policy", _sanitize_snake_id(belief.pillar)],
            },
        )

        plan = PlanSpecArtifact(
            id=plan_id,
            version="1.0",
            description=f"Plan de acción territorial: {bio_text[:150]}",
            preconditions=[],
            steps=[step_1, step_2],
            on_timeout=[],
            on_failure=[],
        )

        return goal, plan

    def compile_and_save(
        self,
        beliefs: list[TerritorialBeliefItem],
        document_id: str,
        document_hash: str,
        only_admitted: bool = True,
    ) -> dict[str, Any]:
        """Compila una lista de creencias curadas y guarda los archivos YAML validados."""
        compiled_goals: list[dict[str, Any]] = []
        compiled_plans: list[dict[str, Any]] = []
        errors: list[str] = []

        for b in beliefs:
            if only_admitted and b.curation_status != "admitted_ebdi":
                continue
            if not only_admitted and b.verification_status != "verified_verbatim":
                continue

            try:
                goal_artifact, plan_artifact = self.compile_belief_to_artifacts(
                    belief=b,
                    document_id=document_id,
                    document_hash=document_hash,
                )

                # Renderizar strings YAML deterministas
                goal_yaml_str = render_goal_yaml(goal_artifact, document_id, document_hash)
                plan_yaml_str = render_plan_yaml(plan_artifact, document_id, document_hash)

                # Validación opcional contra JSON Schema oficial si está disponible
                if self.goal_schema:
                    try:
                        jsonschema.validate(instance=goal_artifact.model_dump(mode="json"), schema=self.goal_schema)
                    except jsonschema.ValidationError as ve:
                        logger.warning(f"Advertencia de esquema GoalSpec en {goal_artifact.id}: {ve.message}")

                if self.plan_schema:
                    try:
                        jsonschema.validate(instance=plan_artifact.model_dump(mode="json"), schema=self.plan_schema)
                    except jsonschema.ValidationError as ve:
                        logger.warning(f"Advertencia de esquema PlanSpec en {plan_artifact.id}: {ve.message}")

                # Guardar archivos físicos en disco
                goal_file = self.goals_dir / f"{goal_artifact.id}.yaml"
                plan_file = self.plans_dir / f"{plan_artifact.id}.yaml"

                goal_file.write_text(goal_yaml_str, encoding="utf-8")
                plan_file.write_text(plan_yaml_str, encoding="utf-8")

                compiled_goals.append({
                    "goal_id": goal_artifact.id,
                    "file_path": _safe_relpath(goal_file),
                    "display_name": goal_artifact.display_name,
                    "pyramid_level": goal_artifact.pyramid_level,
                    "activation_when": goal_artifact.activation_when,
                    "yaml_content": goal_yaml_str,
                })

                compiled_plans.append({
                    "plan_id": plan_artifact.id,
                    "file_path": _safe_relpath(plan_file),
                    "description": plan_artifact.description,
                    "steps_count": len(plan_artifact.steps),
                    "yaml_content": plan_yaml_str,
                })

            except Exception as exc:
                errors.append(f"Error compilando creencia {b.belief_id}: {exc}")
                logger.error(f"Fallo en compilación de creencia {b.belief_id}: {exc}", exc_info=True)

        return {
            "document_id": document_id,
            "document_hash": document_hash,
            "compiled_goals_count": len(compiled_goals),
            "compiled_plans_count": len(compiled_plans),
            "goals": compiled_goals,
            "plans": compiled_plans,
            "errors": errors,
        }
