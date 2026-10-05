from src.application.hooks import validate_invariants, should_use_conflict_prompt


def test_case_004_alarma_false_is_not_ambiguous():
    """Garantiza que 'alarma: false' no dispare la regla de ambigüedad determinista."""
    context = {"nivel": 75, "valvula": "abierta", "alarma": False}
    has_conflict, msg = validate_invariants(context)
    assert has_conflict is False
    assert "invariantes" in msg


def test_case_011_calentador_temperatura_bajando():
    """Garantiza que calentador alto con temperatura bajando se detecte como conflicto térmico."""
    context = {"calentador_pct": 100, "temperatura_crudo": "bajando"}
    has_conflict, msg = validate_invariants(context)
    assert has_conflict is True
    assert "Falla térmica" in msg or "Calentador al máximo" in msg


def test_agronomic_conflict_grain_dilemma():
    """Garantiza detección de colisión venta de grano vs reserva de semilla."""
    context = {
        "agente": "campesino_01",
        "vender_grano": True,
        "reserva_critica": True,
        "escasez_recursos": True
    }
    has_conflict, msg = validate_invariants(context)
    assert has_conflict is True
    assert "Conflicto Agronómico" in msg


def test_agronomic_conflict_deforestation():
    """Garantiza detección de colisión expansión agrícola en zona protegida."""
    context = {
        "expandir_frontera": True,
        "zona_protegida": True
    }
    has_conflict, msg = validate_invariants(context)
    assert has_conflict is True
    assert "degradación del suelo" in msg or "normativa de conservación" in msg


def test_agronomic_conflict_irrigation_drought():
    """Garantiza detección de colisión riego intensivo durante sequía severa."""
    context = {
        "riego_intensivo": True,
        "sequia_severa": True
    }
    has_conflict, msg = validate_invariants(context)
    assert has_conflict is True
    assert "veda hídrica" in msg or "acuífero" in msg


def test_agronomic_conflict_cooperative_breach():
    """Garantiza detección de colisión venta individual vs acuerdo cooperativo."""
    context = {
        "venta_intermediario": True,
        "acuerdo_cooperativo": True
    }
    has_conflict, msg = validate_invariants(context)
    assert has_conflict is True
    assert "acuerdo asociativo" in msg


def test_should_use_conflict_prompt():
    """Verifica el pre-análisis para selección condicional del prompt."""
    assert should_use_conflict_prompt({"dilema_grano": True}) is True
    assert should_use_conflict_prompt({"observacion": "conflicto entre vecinos"}) is True
    assert should_use_conflict_prompt({"situacion": "sequia prolongada"}) is True
    assert should_use_conflict_prompt({"nivel": 50, "presion": 100}) is False


def test_extract_conflict_sources_telemetry():
    """Verifica extracción de fuentes de contexto para conflicto de telemetría."""
    from src.application.hooks import extract_conflict_sources
    from src.domain.schemas import FuenteEnColision
    
    context = {"flujo": 0, "rpm_bomba": 3500}
    has_conflict, msg = validate_invariants(context)
    assert has_conflict is True
    sources = extract_conflict_sources(context, msg)
    assert len(sources) >= 2
    for s in sources:
        assert s["source_type"] == "context_field"
        assert s["source_id"] in ("flujo", "rpm_bomba")
        assert "evidence_ref" in s
        # Validar contra esquema Pydantic
        item = FuenteEnColision(**s)
        assert item.source_id is not None


def test_extract_conflict_sources_documentary():
    """Verifica distinción y extracción de fuentes documentales con cita y hash."""
    from src.application.hooks import extract_conflict_sources
    from src.domain.schemas import FuenteEnColision
    
    context = {
        "dilema_grano": True,
        "vender_grano": True,
        "reserva_critica": True
    }
    has_conflict, msg = validate_invariants(context)
    assert has_conflict is True
    sources = extract_conflict_sources(context, msg)
    assert len(sources) >= 2
    types = [s["source_type"] for s in sources]
    assert "context_field" in types
    assert "document" in types
    
    doc_source = next(s for s in sources if s["source_type"] == "document")
    assert doc_source["source_path"] is not None
    assert doc_source["text_quote"] is not None
    assert doc_source["source_hash"] is not None
    
    # Validar schema
    for s in sources:
        FuenteEnColision(**s)
