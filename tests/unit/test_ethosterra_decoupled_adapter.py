from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.api.src.api.main import app
from src.application.ethosterra_decoupled_adapter import EthosTerraDecoupledAdapter
from src.domain.v2.institutional_schemas import (
    InstitutionalPolicySpec,
    ParametricEquationSpec,
)

client = TestClient(app)


def test_decoupled_adapter_bundle_export(tmp_path):
    adapter = EthosTerraDecoupledAdapter(sandbox_base_dir=tmp_path)

    goals = [
        {
            "id": "goal_test_01",
            "yaml_content": "id: goal_test_01\npyramid_level: SURVIVAL\n",
            "document_id": "doc_01",
            "document_hash": "hash_01",
        }
    ]
    plans = [
        {
            "id": "plan_test_01",
            "yaml_content": "id: plan_test_01\nsteps: []\n",
        }
    ]
    policy = InstitutionalPolicySpec(
        id="policy_credito_01",
        version="1.0",
        display_name="Crédito FINAGRO con Alivio",
        description="Crédito rural con tasa preferencial para productores PDET.",
        policy_domain="credit_bank",
        target_institution="BankOffice",
        activation_condition="state.peasantProfile.loanAmountToPay > 0",
        static_parameters={"tasa_preferencial": 0.04},
        normative_tags=["montes_de_maria"],
        document_source_id="doc_01",
        document_source_hash="hash_01",
        equations=[
            ParametricEquationSpec(
                equation_id="tasa_subsidio",
                expression="0.10 * (1.0 - 0.5 * asociatividad)",
                input_vars=["asociatividad"],
                output_var="tasa",
                domain_bounds={"asociatividad": [0.0, 1.0]},
                range_bounds=[0.01, 0.15],
                monotonicity="decreasing",
            )
        ],
    )

    bundle = adapter.export_bundle(
        goals_yaml=goals,
        plans_yaml=plans,
        institutional_policies=[policy],
        bundle_id="bundle_unit_test",
    )

    assert bundle["bundle_id"] == "bundle_unit_test"
    assert bundle["status"] == "admitted_for_simulation"
    assert bundle["counts"]["goals"] == 1
    assert bundle["counts"]["plans"] == 1
    assert bundle["counts"]["institutional_policies"] == 1

    # Verificar que los archivos físicos existen en tmp_path
    assert (tmp_path / "goals" / "goal_test_01.yaml").exists()
    assert (tmp_path / "plans" / "plan_test_01.yaml").exists()
    assert (tmp_path / "institutional" / "policy_credito_01.yaml").exists()
    assert (tmp_path / "world_modifiers.json").exists()
    assert (tmp_path / "bundle_manifest.json").exists()

    # Verificar que world_modifiers contiene la política bajo credit_bank
    wm_data = json.loads((tmp_path / "world_modifiers.json").read_text(encoding="utf-8"))
    assert "policy_credito_01" in wm_data["credit_bank"]
    assert wm_data["credit_bank"]["policy_credito_01"]["target_institution"] == "BankOffice"


def test_api_verify_equation_endpoint_success():
    payload = {
        "equation_id": "tasa_credito_pdet",
        "expression": "r_base * (1.0 - delta * capital_social)",
        "input_vars": ["capital_social"],
        "output_var": "tasa_interes",
        "parameters": {"r_base": 0.12, "delta": 0.25},
        "domain_bounds": {"capital_social": [0.0, 1.0]},
        "range_bounds": [0.05, 0.15],
        "monotonicity": "decreasing",
        "description": "Alivio crediticio por capital social",
    }
    response = client.post("/v2/atlas/equations/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["equation_id"] == "tasa_credito_pdet"
    assert data["is_valid"] is True
    assert data["monotonicity_satisfied"] is True
    assert len(data["sample_points"]) > 0


def test_api_verify_equation_endpoint_blocks_code_injection():
    malicious_payload = {
        "equation_id": "ataque_inyeccion",
        "expression": "__import__('os').system('echo hacked')",
        "input_vars": ["x"],
        "output_var": "y",
        "domain_bounds": {"x": [0.0, 1.0]},
        "range_bounds": [0.0, 1.0],
    }
    response = client.post("/v2/atlas/equations/verify", json=malicious_payload)
    assert response.status_code == 422
    assert "Violación de seguridad" in response.json()["detail"]


def test_api_export_sandbox_bundle_endpoint():
    response = client.post("/v2/atlas/export/sandbox-bundle", json=[])
    # Puede ser 200 si hay contexto o procesarse con éxito
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = response.json()
        assert "bundle_id" in data
        assert data["status"] == "admitted_for_simulation"


def test_api_get_compiled_yamls_includes_institutional():
    response = client.get("/v2/atlas/artifacts/art_patr_montes_de_maria/compiled-yamls")
    assert response.status_code == 200
    data = response.json()
    assert "goals" in data
    assert "plans" in data
    assert "institutional" in data
