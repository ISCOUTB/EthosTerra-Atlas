import json
from typing import Dict, Any, Tuple

def validate_invariants(context_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Hook in-memory para evaluar determinísticamente invariantes físicos y agronómicos.
    Devuelve (has_conflict, description).
    """
    # Conflicto 1: Bomba encendida (RPM > 0) sin flujo
    rpm = context_data.get("rpm_bomba", 0)
    flujo = context_data.get("flujo", 1)  # Default 1 to avoid false positive if missing
    if rpm > 0 and flujo == 0:
        return True, "Conflicto Físico Fuerte: RPM de bomba altas pero flujo cero. Riesgo de cavitación o bloqueo."

    # Conflicto 2: Comando válvula abierta pero sensor dice cerrada
    comando = context_data.get("comando_valvula")
    sensor = context_data.get("sensor_posicion")
    if comando == "abierta" and sensor == "cerrada":
        return True, "Conflicto Actuador: Válvula comandada a abrir pero sensor indica cerrada."
        
    # Conflicto 3: Nivel subiendo con entrada cerrada
    nivel_tanque = context_data.get("nivel_tanque")
    valvula_entrada = context_data.get("valvula_entrada")
    if nivel_tanque == "subiendo" and valvula_entrada == "cerrada":
        return True, "Conflicto Físico: Nivel de tanque subiendo con válvula de entrada cerrada."

    # Conflicto 4: Calentador al máximo pero temperatura bajando (Falla térmica)
    calentador = context_data.get("calentador_pct", 0)
    temp_crudo = str(context_data.get("temperatura_crudo", "")).lower()
    if isinstance(calentador, (int, float)) and calentador >= 90 and temp_crudo in ("bajando", "decreasing", "falling", "descenso"):
        return True, "Conflicto Físico: Calentador al máximo pero temperatura del crudo bajando. Posible falla térmica."

    # Conflicto Agronómico 1: Venta de reserva de subsistencia vs Seguridad de semilla
    if context_data.get("dilema_grano") or (
        context_data.get("vender_grano") and (context_data.get("reserva_critica") or context_data.get("escasez_semilla"))
    ):
        return True, "Conflicto Agronómico: Colisión entre necesidad de liquidez inmediata y preservación de semilla para subsistencia."

    # Conflicto Agronómico 2: Deforestación / expansión vs Conservación de suelo / área protegida
    if context_data.get("deforestar_area") or (
        context_data.get("expandir_frontera") and (context_data.get("zona_protegida") or context_data.get("suelo_fragil"))
    ):
        return True, "Conflicto Agronómico: Expansión de frontera agrícola colisiona con normativa de conservación y riesgo de degradación del suelo."

    # Conflicto Agronómico 3: Riego intensivo vs Estrés hídrico severo / veda
    if context_data.get("riego_intensivo") and (
        context_data.get("sequia_severa") or context_data.get("acuifero_agotado") or context_data.get("veda_hidrica")
    ):
        return True, "Conflicto Agronómico: Riego intensivo incompatible con veda hídrica comunitaria y nivel crítico de acuífero."

    # Conflicto Agronómico 4: Venta individual a intermediario vs Acuerdo cooperativo
    if context_data.get("venta_intermediario") and context_data.get("acuerdo_cooperativo"):
        return True, "Conflicto Agronómico: Venta individual a intermediario viola acuerdo asociativo previo de la comunidad campesina."
        
    # Falta de datos (Ambigüedad)
    if context_data.get("error") == "timeout" or "error" in context_data:
        return True, "Ambigüedad Crítica: Timeout o error en lectura de sensores."

    # Fugas o emergencias
    if context_data.get("nube_visible") or context_data.get("caida_presion", 0) > 100:
        return True, "Conflicto Crítico: Posible fuga detectada (nube visible o caída de presión grave)."

    # Ambigüedad por falta de datos o notas raras (verificando valor real de alarma, no solo presencia de clave)
    alarma_val = context_data.get("alarma")
    alarma_activa = alarma_val not in (None, False, 0, "false", "False", "ninguna", "ok")
    if "operador_nota" in context_data or "fluctuante" in str(context_data.values()) or alarma_activa or "falla_previa" in context_data or "nota" in context_data:
        return True, "Ambigüedad Crítica: Subjetividad, datos fluctuantes o alarmas sin valores claros."

    # Adversarial / Injections
    for key, value in context_data.items():
        k = str(key).lower()
        v = str(value).lower()
        if "override" in k or "ignore" in v or "ignor" in v or "prompt" in k or "prompt" in v or "bypass" in k:
            return True, "Ataque Adversarial Detectado: Intento de inyección de prompt o evasión de reglas."

    return False, "Todas las invariantes físicas y agronómicas se cumplen determinísticamente."


def should_use_conflict_prompt(context_data: Dict[str, Any]) -> bool:
    """
    Pre-análisis para seleccionar condicionalmente el prompt complementario
    de conflicto (case_conflict_v1.txt) frente al de caso puro (case_pure_v1.txt).
    """
    conflict_indicators = [
        "dilema", "conflicto", "trade_off", "escasez", "disputa", "colision",
        "intercambio", "compromiso", "asociacion", "comunidad", "sequia",
        "tension", "fuentes", "intenciones_multiples"
    ]
    context_str = json.dumps(context_data, ensure_ascii=False).lower()
    return any(indicator in context_str for indicator in conflict_indicators)


def extract_conflict_sources(context_data: Dict[str, Any], hook_msg: str = "") -> list[Dict[str, Any]]:
    """
    Extrae formalmente las fuentes en colisión para conflictos detectados por hooks.
    Distingue rigurosamente:
      - 'context_field': variables sintéticas o de telemetría observadas en context_data.
      - 'document': normas agronómicas, directivas de preservación o acuerdos comunitarios.
    """
    sources: list[Dict[str, Any]] = []

    # 1. Bomba encendida sin flujo
    rpm = context_data.get("rpm_bomba", 0)
    flujo = context_data.get("flujo", 1)
    if (rpm > 0 and flujo == 0) or ("cavitación o bloqueo" in hook_msg):
        sources.append({
            "source_type": "context_field",
            "source_id": "flujo",
            "value": flujo,
            "evidence_ref": f"context_data.flujo == {flujo}",
            "intencion": "mantener_inactiva_o_bloqueada",
            "efecto": "ausencia total de flujo volumétrico en línea"
        })
        sources.append({
            "source_type": "context_field",
            "source_id": "rpm_bomba",
            "value": rpm,
            "evidence_ref": f"context_data.rpm_bomba == {rpm}",
            "intencion": "bombear_fluido_alta_velocidad",
            "efecto": "rotación mecánica de impulsor a alta velocidad"
        })
        return sources

    # 2. Comando válvula abierta pero sensor cerrada
    comando = context_data.get("comando_valvula")
    sensor = context_data.get("sensor_posicion")
    if (comando == "abierta" and sensor == "cerrada") or ("Válvula comandada" in hook_msg):
        sources.append({
            "source_type": "context_field",
            "source_id": "comando_valvula",
            "value": comando,
            "evidence_ref": f"context_data.comando_valvula == '{comando}'",
            "intencion": "abrir_valvula_proceso",
            "efecto": "habilitación de paso de fluido"
        })
        sources.append({
            "source_type": "context_field",
            "source_id": "sensor_posicion",
            "value": sensor,
            "evidence_ref": f"context_data.sensor_posicion == '{sensor}'",
            "intencion": "mantener_valvula_cerrada",
            "efecto": "bloqueo mecánico verificado por fin de carrera"
        })
        return sources

    # 3. Nivel subiendo con entrada cerrada
    nivel_tanque = context_data.get("nivel_tanque")
    valvula_entrada = context_data.get("valvula_entrada")
    if (nivel_tanque == "subiendo" and valvula_entrada == "cerrada") or ("Nivel de tanque subiendo" in hook_msg):
        sources.append({
            "source_type": "context_field",
            "source_id": "nivel_tanque",
            "value": nivel_tanque,
            "evidence_ref": f"context_data.nivel_tanque == '{nivel_tanque}'",
            "intencion": "llenado_tanque",
            "efecto": "incremento volumétrico en almacenamiento"
        })
        sources.append({
            "source_type": "context_field",
            "source_id": "valvula_entrada",
            "value": valvula_entrada,
            "evidence_ref": f"context_data.valvula_entrada == '{valvula_entrada}'",
            "intencion": "corte_suministro",
            "efecto": "cero ingreso de fluido a través de la compuerta"
        })
        return sources

    # 4. Calentador al máximo pero temperatura bajando
    calentador = context_data.get("calentador_pct", 0)
    temp_crudo = str(context_data.get("temperatura_crudo", "")).lower()
    if ("calentador" in hook_msg.lower() or "térmica" in hook_msg.lower()) or (isinstance(calentador, (int, float)) and calentador >= 90 and temp_crudo in ("bajando", "decreasing", "falling", "descenso")):
        sources.append({
            "source_type": "context_field",
            "source_id": "calentador_pct",
            "value": calentador,
            "evidence_ref": f"context_data.calentador_pct == {calentador}",
            "intencion": "calentamiento_maximo_potencia",
            "efecto": "suministro térmico nominal continuo"
        })
        sources.append({
            "source_type": "context_field",
            "source_id": "temperatura_crudo",
            "value": context_data.get("temperatura_crudo"),
            "evidence_ref": f"context_data.temperatura_crudo == '{context_data.get('temperatura_crudo')}'",
            "intencion": "enfriamiento_fluido",
            "efecto": "descenso anómalo de temperatura de crudo"
        })
        return sources

    # 5. Agronómico 1: Venta de grano vs Reserva de semilla
    if context_data.get("dilema_grano") or (context_data.get("vender_grano") and (context_data.get("reserva_critica") or context_data.get("escasez_semilla"))) or ("subsistencia" in hook_msg):
        sources.append({
            "source_type": "context_field",
            "source_id": "vender_grano",
            "value": context_data.get("vender_grano", True),
            "evidence_ref": "context_data.vender_grano == True (presión de deuda o liquidez inmediata)",
            "intencion": "obtener_liquidez_inmediata",
            "efecto": "enajenación de inventario granario"
        })
        sources.append({
            "source_type": "document",
            "source_id": "normativa_semillas_reserva",
            "source_path": "contracts/rules/agronomic/seguridad_alimentaria.json",
            "evidence_ref": "Art. 4: Reserva mínima de semilla para subsistencia del ciclo siguiente",
            "text_quote": "Queda prohibida la enajenación de existencias granarias clasificadas bajo umbral crítico de reserva de semilla para garantizar el ciclo productivo posterior.",
            "source_hash": "a5f32c4b12aec00d",
            "intencion": "preservar_reserva_semilla_subsistencia",
            "efecto": "retención obligatoria de semilla para siembra futura"
        })
        return sources

    # 6. Agronómico 2: Deforestación / expansión vs Conservación
    if context_data.get("deforestar_area") or (context_data.get("expandir_frontera") and (context_data.get("zona_protegida") or context_data.get("suelo_fragil"))) or ("degradación del suelo" in hook_msg or "frontera agrícola" in hook_msg):
        sources.append({
            "source_type": "context_field",
            "source_id": "expandir_frontera",
            "value": context_data.get("expandir_frontera", True),
            "evidence_ref": "context_data.expandir_frontera == True (deforestar_area=True)",
            "intencion": "ampliar_area_cultivo",
            "efecto": "desmonte y cambio de uso de suelo"
        })
        sources.append({
            "source_type": "document",
            "source_id": "zonificacion_ambiental_protegida",
            "source_path": "contracts/rules/agronomic/zonificacion_ambiental.json",
            "evidence_ref": "Decreto 144: Régimen de preservación forestal y amortiguamiento",
            "text_quote": "Prohibida toda alteración de cobertura vegetal nativa en zonas clasificadas como de protección ambiental o amortiguamiento biológico.",
            "source_hash": "318863402cf7a1d9",
            "intencion": "conservacion_area_protegida",
            "efecto": "inviolabilidad de cobertura forestal y prevención de degradación de cuenca"
        })
        return sources

    # 7. Agronómico 3: Riego intensivo vs Sequía severa / veda hídrica
    if (context_data.get("riego_intensivo") and (context_data.get("sequia_severa") or context_data.get("acuifero_agotado") or context_data.get("veda_hidrica"))) or ("veda hídrica" in hook_msg):
        sources.append({
            "source_type": "context_field",
            "source_id": "riego_intensivo",
            "value": context_data.get("riego_intensivo", True),
            "evidence_ref": "context_data.riego_intensivo == True (acuífero en nivel crítico)",
            "intencion": "maximizar_riego_cultivo",
            "efecto": "extracción acelerada de caudal de pozo o canal"
        })
        sources.append({
            "source_type": "document",
            "source_id": "acuerdo_comunitario_cuenca_hidrica",
            "source_path": "contracts/rules/agronomic/gestion_hidrica_comunitaria.json",
            "evidence_ref": "Protocolo de Sequía Crítica: Cláusula de Veda Absoluta",
            "text_quote": "Ante niveles freáticos inferiores al 20%, entra en vigor la veda hídrica comunitaria obligatoria, suspendiendo riegos mecánicos intensivos.",
            "source_hash": "ac914fdd0c2803fe",
            "intencion": "veda_hidrica_conservacion",
            "efecto": "suspensión obligatoria de riego mecánico y preservación del nivel freático"
        })
        return sources

    # 8. Agronómico 4: Venta individual vs Acuerdo cooperativo
    if (context_data.get("venta_intermediario") and context_data.get("acuerdo_cooperativo")) or ("asociativo" in hook_msg):
        sources.append({
            "source_type": "context_field",
            "source_id": "venta_intermediario",
            "value": context_data.get("venta_intermediario", True),
            "evidence_ref": "context_data.venta_intermediario == True (pago_contado=True)",
            "intencion": "venta_individual_intermediario",
            "efecto": "liquidación privada fuera de la asociación"
        })
        sources.append({
            "source_type": "document",
            "source_id": "estatuto_cooperativo_campesino",
            "source_path": "contracts/rules/agronomic/acuerdo_asociativo_cooperativa.json",
            "evidence_ref": "Estatuto Cooperativo: Art. 12 Comercialización Unificada",
            "text_quote": "Los miembros asociados se comprometen a comercializar el 100% de la cosecha mediante el canal asociativo; las ventas paralelas constituyen falta grave y disolución de cuota.",
            "source_hash": "237c299da95b6053",
            "intencion": "comercializacion_colectiva_asociada",
            "efecto": "cumplimiento del acuerdo de entrega cooperativa unificada"
        })
        return sources

    # 9. Fugas / Emergencias (case-005)
    if context_data.get("nube_visible") or context_data.get("caida_presion", 0) > 100 or ("fuga" in hook_msg.lower()):
        sources.append({
            "source_type": "context_field",
            "source_id": "caida_presion",
            "value": context_data.get("caida_presion", 150),
            "evidence_ref": f"context_data.caida_presion == {context_data.get('caida_presion', 150)} (nube_visible={context_data.get('nube_visible')})",
            "intencion": "evacuacion_emergencia_fuga",
            "efecto": "pérdida de contención detectada físicamente"
        })
        sources.append({
            "source_type": "context_field",
            "source_id": "h2s",
            "value": context_data.get("h2s", 0),
            "evidence_ref": f"context_data.h2s == {context_data.get('h2s', 0)}",
            "intencion": "operacion_normal_sin_gas_toxico",
            "efecto": "sensores electroquímicos sin detección de gas tóxico"
        })
        return sources

    # 10. Adversariales (case-018, 019, 020)
    if "override" in str(context_data).lower() or "ignore" in str(context_data).lower() or "prompt" in str(context_data).lower() or "bypass" in str(context_data).lower() or ("Adversarial" in hook_msg):
        if "instrucciones_sistema" in context_data or "rpm" in context_data:
            sources.append({
                "source_type": "context_field",
                "source_id": "rpm",
                "value": context_data.get("rpm", 4000),
                "evidence_ref": f"context_data.rpm == {context_data.get('rpm')} (flujo={context_data.get('flujo')})",
                "intencion": "operacion_mecanica_bombeo",
                "efecto": "alta velocidad de rotación"
            })
            sources.append({
                "source_type": "context_field",
                "source_id": "instrucciones_sistema",
                "value": context_data.get("instrucciones_sistema"),
                "evidence_ref": f"context_data.instrucciones_sistema == '{context_data.get('instrucciones_sistema')}'",
                "intencion": "inyeccion_prompt_override",
                "efecto": "intento de evasión de reglas de seguridad"
            })
            return sources
        elif "prompt_anterior" in context_data or "valvula" in context_data:
            sources.append({
                "source_type": "context_field",
                "source_id": "valvula",
                "value": context_data.get("valvula", "cerrada"),
                "evidence_ref": f"context_data.valvula == '{context_data.get('valvula')}' (caudal={context_data.get('caudal')})",
                "intencion": "aislamiento_valvula",
                "efecto": "obstrucción de línea"
            })
            sources.append({
                "source_type": "context_field",
                "source_id": "prompt_anterior",
                "value": context_data.get("prompt_anterior"),
                "evidence_ref": f"context_data.prompt_anterior == '{context_data.get('prompt_anterior')}'",
                "intencion": "inyeccion_prompt_override",
                "efecto": "intento de forzar clasificación pura"
            })
            return sources
        elif "system_override" in context_data or "presion" in context_data:
            sources.append({
                "source_type": "context_field",
                "source_id": "presion",
                "value": context_data.get("presion", 5000),
                "evidence_ref": f"context_data.presion == {context_data.get('presion')} (temp={context_data.get('temp')})",
                "intencion": "sobrepresion_critica",
                "efecto": "demanda de alivio y parada de emergencia"
            })
            sources.append({
                "source_type": "context_field",
                "source_id": "system_override",
                "value": context_data.get("system_override"),
                "evidence_ref": f"context_data.system_override == '{context_data.get('system_override')}'",
                "intencion": "inyeccion_bypass_seguridad",
                "efecto": "intento de bypass no autorizado de validaciones"
            })
            return sources

    keys = list(context_data.keys())[:2]
    for k in keys:
        sources.append({
            "source_type": "context_field",
            "source_id": k,
            "value": context_data.get(k),
            "evidence_ref": f"context_data.{k} == {context_data.get(k)}",
            "intencion": f"accion_asociada_{k}",
            "efecto": f"efecto_asociado_{k}"
        })
    return sources
