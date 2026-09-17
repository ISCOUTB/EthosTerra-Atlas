from __future__ import annotations

import re
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict


class ActivationValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    raw_expression: str
    syntax_valid: bool
    syntax_errors: list[str]
    runtime_compatible: Literal["yes", "no", "unknown"]
    requires_simulation_test: bool
    detected_methods: list[str]
    detected_operators: list[str]
    notes: str


KNOWN_METHODS = {
    "hasLandWithSeason",
    "has_land_with_season",
    "hasLandWithKind",
    "has_land_with_kind",
    "hasLandWithCropCare",
    "has_land_with_crop_care",
    "hasLandWithKindAndSeason",
    "has_land_with_kind_and_season",
    "hasHarvestedWeight",
    "has_harvested_weight",
    "has_money_below",
    "is_sunday",
}

KNOWN_OPERATORS = ["&&", "||", "!", "==", "!=", "<=", ">=", "<", ">"]


def validate_activation_when(expression: str) -> ActivationValidationResult:
    expr = expression.strip()
    errors: list[str] = []

    if not expr:
        return ActivationValidationResult(
            raw_expression=expr,
            syntax_valid=False,
            syntax_errors=["Expresión de activación vacía."],
            runtime_compatible="no",
            requires_simulation_test=True,
            detected_methods=[],
            detected_operators=[],
            notes="La expresión no puede ser vacía."
        )

    # Detección de operadores
    found_ops = [op for op in KNOWN_OPERATORS if op in expr]

    # Detección de métodos llamados sobre state / belief
    method_matches = re.findall(r"(?:state|belief)\.([a-zA-Z0-9_]+)\s*\(", expr)
    found_methods = list(set(method_matches))

    # Comprobación sintáctica básica
    # Paréntesis balanceados
    if expr.count("(") != expr.count(")"):
        errors.append("Paréntesis desbalanceados en la expresión.")

    # Comillas balanceadas
    if (expr.count("'") % 2 != 0) or (expr.count('"') % 2 != 0):
        errors.append("Comillas desbalanceadas en literales de texto.")

    # Simulación de la transformación que hace yaml_evaluator.py de EthosTerra
    transformed = expr
    transformed = transformed.replace('&&', ' and ').replace('||', ' or ')
    transformed = re.sub(r'!(\w)', r'not \1', transformed)
    transformed = re.sub(r'!\s*\(', 'not (', transformed)
    transformed = re.sub(r'belief\.get\(\s*[\'"](\w+)[\'"]\s*\)', r'state.\1', transformed)

    # Compilación estática de la expresión Python resultante para validar gramática
    try:
        compile(transformed, "<activation_when>", "eval")
        syntax_valid = len(errors) == 0
    except SyntaxError as se:
        errors.append(f"Error de sintaxis Python tras normalización MVEL2: {se}")
        syntax_valid = False

    return ActivationValidationResult(
        raw_expression=expr,
        syntax_valid=syntax_valid,
        syntax_errors=errors,
        runtime_compatible="unknown",
        requires_simulation_test=True,
        detected_methods=found_methods,
        detected_operators=found_ops,
        notes="La compatibilidad estática fue verificada; la ejecución en runtime requiere prueba en simulación viva."
    )
