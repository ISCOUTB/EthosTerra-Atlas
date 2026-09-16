from typing import Dict, Any, Tuple

def validate_invariants(context_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Hook in-memory para evaluar determinísticamente invariantes físicos.
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
        
    # Falta de datos (Ambigüedad)
    if context_data.get("error") == "timeout" or "error" in context_data:
        return True, "Ambigüedad Crítica: Timeout o error en lectura de sensores."

    # Fugas o emergencias
    if context_data.get("nube_visible") or context_data.get("caida_presion", 0) > 100:
        return True, "Conflicto Crítico: Posible fuga detectada (nube visible o caída de presión grave)."

    # Ambigüedad por falta de datos o notas raras
    if "operador_nota" in context_data or "fluctuante" in str(context_data.values()) or "alarma" in context_data or "falla_previa" in context_data or "nota" in context_data:
        return True, "Ambigüedad Crítica: Subjetividad, datos fluctuantes o alarmas sin valores claros."

    # Adversarial / Injections
    for key, value in context_data.items():
        k = str(key).lower()
        v = str(value).lower()
        if "override" in k or "ignore" in v or "ignor" in v or "prompt" in k or "prompt" in v or "bypass" in k:
            return True, "Ataque Adversarial Detectado: Intento de inyección de prompt o evasión de reglas."

    return False, "Todas las invariantes físicas se cumplen determinísticamente."
