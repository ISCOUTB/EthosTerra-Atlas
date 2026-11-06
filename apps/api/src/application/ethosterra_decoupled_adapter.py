from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from src.domain.v2.institutional_schemas import InstitutionalPolicySpec

logger = logging.getLogger("ethosterra_decoupled_adapter")


class AdapterExportError(Exception):
    """Error al empaquetar especificaciones para el simulador desacoplado."""


def compute_sha256(content: str | bytes) -> str:
    """Calcula el hash SHA-256 de una cadena o bloque de bytes."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


class EthosTerraDecoupledAdapter:
    """Adaptador desacoplado de integración entre el Atlas Territorial y el simulador EthosTerra.

    Garantiza la preservación biofísica y soberanía del simulador:
    - Escribe exclusivamente en el directorio de sandbox ('outputs/simulation_sandbox/').
    - Genera especificaciones declarativas validadas (GoalSpec, PlanSpec, InstitutionalPolicySpec).
    - Agrega moduladores institucionales a 'world_modifiers.json' para consumo seguro por BESA.
    """

    def __init__(self, sandbox_base_dir: Path | None = None):
        self.sandbox_dir = (sandbox_base_dir or Path("outputs/simulation_sandbox")).resolve()
        self.goals_dir = self.sandbox_dir / "goals"
        self.plans_dir = self.sandbox_dir / "plans"
        self.institutional_dir = self.sandbox_dir / "institutional"

        # Asegurar directorios de destino
        self.goals_dir.mkdir(parents=True, exist_ok=True)
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        self.institutional_dir.mkdir(parents=True, exist_ok=True)

    def render_institutional_yaml(self, policy: InstitutionalPolicySpec) -> str:
        """Serializa una especificación institucional a YAML canónico y ordenado."""
        data = policy.model_dump(mode="json")
        header = (
            f"# InstitutionalPolicySpec: {policy.id}\n"
            f"# Documento de Origen: {policy.document_source_id}\n"
            f"# Hash de Aprobación: {policy.document_source_hash}\n"
            f"# Fecha de Generación: {datetime.now(timezone.utc).isoformat()}\n\n"
        )
        body = yaml.dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False)
        return header + body

    def export_bundle(
        self,
        goals_yaml: list[dict[str, str]],
        plans_yaml: list[dict[str, str]],
        institutional_policies: list[InstitutionalPolicySpec],
        bundle_id: str | None = None,
    ) -> dict[str, Any]:
        """Empaqueta y exporta un conjunto completo de artefactos hacia el sandbox de simulación."""
        timestamp = datetime.now(timezone.utc).isoformat()
        b_id = bundle_id or f"bundle_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        files_inventory: list[dict[str, Any]] = []
        source_docs: dict[str, str] = {}

        # 1. Exportar GoalSpecs
        for g in goals_yaml:
            goal_id = g.get("id", "unnamed_goal")
            content = g.get("yaml_content", "")
            doc_id = g.get("document_id", "unknown")
            doc_hash = g.get("document_hash", "")
            if doc_id != "unknown":
                source_docs[doc_id] = doc_hash

            dest_path = self.goals_dir / f"{goal_id}.yaml"
            dest_path.write_text(content, encoding="utf-8")
            files_inventory.append({
                "path": str(dest_path.relative_to(self.sandbox_dir)),
                "artifact_type": "goal_spec",
                "sha256": compute_sha256(content),
            })

        # 2. Exportar PlanSpecs
        for p in plans_yaml:
            plan_id = p.get("id", "unnamed_plan")
            content = p.get("yaml_content", "")
            dest_path = self.plans_dir / f"{plan_id}.yaml"
            dest_path.write_text(content, encoding="utf-8")
            files_inventory.append({
                "path": str(dest_path.relative_to(self.sandbox_dir)),
                "artifact_type": "plan_spec",
                "sha256": compute_sha256(content),
            })

        # 3. Exportar InstitutionalPolicySpecs y compilar world_modifiers
        world_modifiers: dict[str, Any] = {
            "credit_bank": {},
            "market_pricing": {},
            "civic_subsidies": {},
            "water_quota": {},
            "agro_extension": {},
        }

        for pol in institutional_policies:
            yaml_str = self.render_institutional_yaml(pol)
            dest_path = self.institutional_dir / f"{pol.id}.yaml"
            dest_path.write_text(yaml_str, encoding="utf-8")
            source_docs[pol.document_source_id] = pol.document_source_hash

            files_inventory.append({
                "path": str(dest_path.relative_to(self.sandbox_dir)),
                "artifact_type": "institutional_policy",
                "sha256": compute_sha256(yaml_str),
            })

            # Inyectar en los modificadores del mundo
            domain = pol.policy_domain
            domain_dict = world_modifiers.setdefault(domain, {})
            domain_dict[pol.id] = {
                "target_institution": pol.target_institution,
                "activation_condition": pol.activation_condition,
                "static_parameters": pol.static_parameters,
                "equations": [eq.model_dump(mode="json") for eq in pol.equations],
            }

        # 4. Escribir world_modifiers.json
        wm_path = self.sandbox_dir / "world_modifiers.json"
        wm_content = json.dumps(world_modifiers, indent=2, ensure_ascii=False)
        wm_path.write_text(wm_content, encoding="utf-8")
        files_inventory.append({
            "path": str(wm_path.relative_to(self.sandbox_dir)),
            "artifact_type": "world_modifiers",
            "sha256": compute_sha256(wm_content),
        })

        # 5. Generar Manifiesto Canónico del Bundle
        manifest_data = {
            "bundle_id": b_id,
            "generated_at": timestamp,
            "version": "1.0",
            "source_documents": [
                {"document_id": did, "document_hash": dhash} for did, dhash in source_docs.items()
            ],
            "counts": {
                "goals": len(goals_yaml),
                "plans": len(plans_yaml),
                "institutional_policies": len(institutional_policies),
                "total_files": len(files_inventory),
            },
            "files": files_inventory,
            "status": "admitted_for_simulation",
        }

        manifest_path = self.sandbox_dir / "bundle_manifest.json"
        manifest_content = json.dumps(manifest_data, indent=2, ensure_ascii=False)
        manifest_path.write_text(manifest_content, encoding="utf-8")

        return manifest_data
