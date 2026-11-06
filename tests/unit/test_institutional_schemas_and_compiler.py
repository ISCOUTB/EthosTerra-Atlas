from __future__ import annotations

import pytest
from pydantic import ValidationError

from apps.atlas.compilers.ebdi_yaml_compiler import EBDIYamlCompiler
from apps.atlas.schemas.context_schemas import TerritorialBeliefItem
from src.domain.v2.institutional_schemas import (
    InstitutionalPolicySpec,
    ParametricEquationSpec,
)


def test_parametric_equation_spec_valid():
    spec = ParametricEquationSpec(
        equation_id="tasa_alivio_cartera",
        expression="tasa_base * (1.0 - factor_asociado)",
        input_vars=["factor_asociado"],
        output_var="tasa_final",
        parameters={"tasa_base": 0.15},
        domain_bounds={"factor_asociado": [0.0, 1.0]},
        range_bounds=[0.0, 0.20],
        monotonicity="decreasing",
    )
    assert spec.equation_id == "tasa_alivio_cartera"
    assert spec.parameters["tasa_base"] == 0.15


def test_parametric_equation_spec_rejects_invalid_id():
    with pytest.raises(ValidationError):
        ParametricEquationSpec(
            equation_id="Tasa-Invalida!",
            expression="x + 1",
            input_vars=["x"],
            output_var="y",
            domain_bounds={"x": [0.0, 1.0]},
            range_bounds=[0.0, 2.0],
        )


def test_parametric_equation_spec_rejects_extra_fields():
    with pytest.raises(ValidationError):
        ParametricEquationSpec(
            equation_id="eq_valida",
            expression="x + 1",
            input_vars=["x"],
            output_var="y",
            domain_bounds={"x": [0.0, 1.0]},
            range_bounds=[0.0, 2.0],
            campo_no_permitido="inyeccion",  # extra='forbid'
        )


def test_institutional_policy_spec_valid():
    pol = InstitutionalPolicySpec(
        id="politica_alivio_finagro_montes_de_maria",
        version="1.0",
        display_name="Línea Especial de Crédito con Tasa Subsidiada",
        description="Subsidio de tasa de interés para pequeños productores en zonas PDET.",
        knowledge_tier="institutional_policy",
        policy_domain="credit_bank",
        target_institution="BankOffice",
        activation_condition="state.peasantProfile.loanAmountToPay > 0",
        static_parameters={"subsidio_pct": 0.4},
        normative_tags=["pdet_montes_de_maria", "finagro_lec"],
        document_source_id="art_patr_montes_de_maria",
        document_source_hash="abcdef1234567890",
    )
    assert pol.target_institution == "BankOffice"
    assert pol.policy_domain == "credit_bank"


def test_ebdi_yaml_compiler_maps_institutional_domains(tmp_path):
    compiler = EBDIYamlCompiler(output_base_dir=tmp_path)

    # Caso 1: Crédito / Banco
    belief_bank = TerritorialBeliefItem(
        belief_id="bel_test_001",
        source_id="doc_patr_01",
        pillar="reactivacion_economica",
        topic="Crédito rural asociativo",
        belief_key="tasa_preferencial_credito",
        raw_excerpt="Se otorgarán créditos Finagro con tasa subsidiada.",
        ebdi_belief_assertion="Tasa de interés reducida para créditos Finagro.",
        confidence=0.95,
        verification_status="verified_verbatim",
        knowledge_tier="institutional_policy",
    )
    pol_bank = compiler.compile_belief_to_institutional_policy(
        belief=belief_bank,
        document_id="doc_patr_01",
        document_hash="hash_01",
    )
    assert pol_bank.policy_domain == "credit_bank"
    assert pol_bank.target_institution == "BankOffice"

    # Caso 2: Precio / Mercado
    belief_market = TerritorialBeliefItem(
        belief_id="bel_test_002",
        source_id="doc_pidaret_01",
        pillar="comercializacion",
        topic="Precio de sustentación de cosechas",
        belief_key="precio_minimo_yuca",
        raw_excerpt="Establecimiento de precios mínimos para compra pública de yuca.",
        ebdi_belief_assertion="Compra local de yuca a precio de sustentación.",
        confidence=0.90,
        verification_status="verified_verbatim",
        knowledge_tier="institutional_policy",
    )
    pol_market = compiler.compile_belief_to_institutional_policy(
        belief=belief_market,
        document_id="doc_pidaret_01",
        document_hash="hash_02",
    )
    assert pol_market.policy_domain == "market_pricing"
    assert pol_market.target_institution == "MarketPlace"

    # Caso 3: Agua / Riego
    belief_water = TerritorialBeliefItem(
        belief_id="bel_test_003",
        source_id="doc_pot_01",
        pillar="gestion_del_agua",
        topic="Cuotas y distritos de riego",
        belief_key="distrito_riego_maria_la_baja",
        raw_excerpt="Regulación del caudal y cuotas de agua para riego comunitario.",
        ebdi_belief_assertion="Acceso regulado al distrito de riego en María La Baja.",
        confidence=0.88,
        verification_status="verified_verbatim",
        knowledge_tier="institutional_policy",
    )
    pol_water = compiler.compile_belief_to_institutional_policy(
        belief=belief_water,
        document_id="doc_pot_01",
        document_hash="hash_03",
    )
    assert pol_water.policy_domain == "water_quota"
    assert pol_water.target_institution == "AgroEcosystem"


def test_compiler_saves_institutional_yaml_file(tmp_path):
    compiler = EBDIYamlCompiler(output_base_dir=tmp_path)

    belief = TerritorialBeliefItem(
        belief_id="bel_save_001",
        source_id="doc_test_save",
        pillar="infraestructura_y_maquinaria",
        topic="Banco de maquinaria comunitaria",
        belief_key="subsidio_tractor_comunal",
        raw_excerpt="Subsidio del 50% en horas de tractor para labranza.",
        ebdi_belief_assertion="Acceso a maquinaria comunitaria para pequeños productores.",
        confidence=0.92,
        verification_status="verified_verbatim",
        curation_status="admitted_ebdi",
        knowledge_tier="institutional_policy",
    )

    result = compiler.compile_and_save(
        beliefs=[belief],
        document_id="doc_test_save",
        document_hash="hash_test_save",
        only_admitted=True,
    )

    assert result["compiled_institutional_count"] == 1
    assert result["compiled_goals_count"] == 1
    assert len(result["institutional"]) == 1

    # Verificar que el archivo YAML físico fue escrito en el directorio institutional
    yaml_files = list(compiler.institutional_dir.glob("*.yaml"))
    assert len(yaml_files) == 1
    content = yaml_files[0].read_text(encoding="utf-8")
    assert "InstitutionalPolicySpec:" in content
    assert "target_institution: CivicAuthority" in content
    assert "policy_domain: civic_subsidies" in content
