import json
import pytest
import jsonschema
from pathlib import Path
from pydantic import ValidationError

from src.domain.schemas import CasoConflictivo, FuenteEnColision


def get_conflict_schema() -> dict:
    # Resolves path to contracts/schemas/caso-conflictivo.schema.json
    schema_path = Path(__file__).resolve().parents[2] / "contracts" / "schemas" / "caso-conflictivo.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_legacy_caso_conflictivo_compatibility():
    """Garantiza que instancias creadas con los campos mínimos de S5/S6 sigan siendo válidas."""
    c = CasoConflictivo(
        tipo="conflicto",
        conflicto_detectado="Conflicto físico: RPM altas sin flujo",
        opciones_resolucion=["Apagar bomba", "Abrir válvula"],
        requiere_humano=True
    )
    assert c.tipo == "conflicto"
    assert c.conflicto_detectado == "Conflicto físico: RPM altas sin flujo"
    assert c.descripcion_contradiccion == "Conflicto físico: RPM altas sin flujo"
    assert c.requiere_humano is True
    assert c.fuentes_en_colision == []


def test_enriched_caso_conflictivo_s7_s8():
    """Garantiza que instancias enriquecidas para S7-S8 se creen con tipado estricto."""
    fuente1 = FuenteEnColision(
        fuente_id="regla_vender_grano",
        intencion="vender_reserva_grano",
        efecto="obtener liquidez inmediata de $500",
        evidencia="precio de mercado actual favorable"
    )
    fuente2 = FuenteEnColision(
        fuente_id="norma_seguridad_alimentaria",
        intencion="reservar_semilla",
        efecto="garantizar siembra del siguiente ciclo agrícola",
        evidencia="reserva de semilla por debajo del umbral mínimo"
    )

    c = CasoConflictivo(
        tipo="conflicto",
        conflicto_detectado="Colisión entre liquidez a corto plazo y sostenibilidad agrícola",
        titulo_conflicto="Venta vs Reserva de Grano",
        ubicacion="Sector A - Silo 2",
        ruta_archivo_colisionado="reglas/agricolas/prioridades_campesinas.json",
        fuentes_en_colision=[fuente1, fuente2],
        opciones_resolucion=["Venta parcial del 30%", "Mantener reserva total"],
        confidence=0.95,
        requiere_humano=True,
        razonamiento="Ambas intenciones son incompatibles bajo el detonante de escasez de recursos."
    )

    assert c.titulo_conflicto == "Venta vs Reserva de Grano"
    assert len(c.fuentes_en_colision) == 2
    assert c.fuentes_en_colision[0].fuente_id == "regla_vender_grano"


def test_reconciliation_validator():
    """Verifica que 'descripcion_contradiccion' y 'requires_human_review' se reconcilien automáticamente."""
    data = {
        "tipo": "conflicto",
        "descripcion_contradiccion": "Incompatibilidad detectada por modelo LLM",
        "opciones_resolucion": ["Revisión manual"],
        "requires_human_review": True
    }
    c = CasoConflictivo.model_validate(data)
    assert c.conflicto_detectado == "Incompatibilidad detectada por modelo LLM"
    assert c.descripcion_contradiccion == "Incompatibilidad detectada por modelo LLM"
    assert c.requiere_humano is True


def test_extra_fields_forbidden():
    """Verifica que el modelo rechace campos inesperados (extra='forbid')."""
    with pytest.raises(ValidationError):
        CasoConflictivo(
            tipo="conflicto",
            conflicto_detectado="Test",
            opciones_resolucion=["Opcion 1"],
            campo_inexistente="alucinacion"
        )


def test_json_schema_validation_positive():
    """Valida que una respuesta conforme al schema JSON Draft-07 sea aceptada."""
    schema = get_conflict_schema()

    valid_payload = {
        "tipo": "conflicto",
        "titulo_conflicto": "Dilema de siembra temprana vs sequía",
        "descripcion_contradiccion": "Intención de preparar tierra choca con alerta de sequía prolongada.",
        "ubicacion": "Parcela Norte",
        "ruta_archivo_colisionado": "rules/normativa_sequia.json",
        "fuentes_en_colision": [
            {
                "fuente_id": "calendario_agricola",
                "intencion": "iniciar_preparacion_suelo",
                "efecto": "inversión de combustible y jornales",
                "evidencia": "inicio de mes de siembra histórico"
            },
            {
                "fuente_id": "alerta_agroclimatica",
                "intencion": "posponer_labores",
                "efecto": "evitar pérdida de inversión por ausencia de precipitaciones",
                "evidencia": "pronóstico de 45 días sin lluvia"
            }
        ],
        "opciones_resolucion": [
            "Posponer labores 15 días",
            "Instalar sistema de riego de emergencia",
            "Proceder asumiendo riesgo"
        ],
        "confidence": 0.92,
        "requires_human_review": True,
        "razonamiento": "No es posible sembrar sin humedad suficiente; continuar implica pérdida total.",
        "warnings": [],
        "trace_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
        "model_name": "ai/gemma4:E4B",
        "model_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "latency_ms": 12.5
    }

    # Debe validar sin excepciones
    jsonschema.validate(instance=valid_payload, schema=schema)


def test_json_schema_validation_negative_min_sources():
    """Valida que el schema rechace conflictos con menos de dos fuentes en colisión."""
    schema = get_conflict_schema()

    invalid_payload = {
        "tipo": "conflicto",
        "titulo_conflicto": "Conflicto inválido",
        "descripcion_contradiccion": "Una sola fuente no constituye conflicto de intenciones.",
        "ubicacion": None,
        "ruta_archivo_colisionado": None,
        "fuentes_en_colision": [
            {
                "fuente_id": "unica_fuente",
                "intencion": "hacer_algo",
                "efecto": "efecto x"
            }
        ],
        "opciones_resolucion": ["Opcion 1"],
        "confidence": 0.8,
        "requires_human_review": True,
        "razonamiento": "Prueba",
        "warnings": [],
        "trace_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
        "model_name": "ai/gemma4:E4B",
        "model_digest": "sha256:1234",
        "latency_ms": 10.0
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_payload, schema=schema)
