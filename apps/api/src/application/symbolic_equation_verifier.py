from __future__ import annotations

import ast
import math
from typing import Any

from src.domain.v2.institutional_schemas import (
    ParametricEquationSpec,
    VerificationReport,
)


class SecurityViolationError(Exception):
    """Excepción al detectar construcciones de código prohibidas en una ecuación simbólica."""


class EquationVerificationError(Exception):
    """Excepción cuando una ecuación no satisface sus propiedades numéricas requeridas."""


ALLOWED_MATH_FUNCTIONS = {
    "exp": math.exp,
    "log": math.log,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "min": min,
    "max": max,
    "abs": abs,
    "floor": math.floor,
    "ceil": math.ceil,
}

ALLOWED_AST_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Name,
    ast.Constant,
    ast.Call,
    ast.Load,
    # Operadores aritméticos
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.USub,
    ast.UAdd,
)


class SymbolicEquationVerifier:
    """Verificador seguro de propiedades matemáticas para relaciones institucionales generadas."""

    def __init__(self, num_samples: int = 100, tolerance: float = 1e-7):
        self.num_samples = num_samples
        self.tolerance = tolerance

    def validate_ast_safety(self, expression: str) -> ast.Expression:
        """Inspecciona el AST para asegurar que la expresión sea exclusivamente matemática pura."""
        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as e:
            raise SecurityViolationError(f"Sintaxis inválida en expresión matemática: {e}") from e

        for node in ast.walk(tree):
            if not isinstance(node, ALLOWED_AST_NODES):
                raise SecurityViolationError(
                    f"Nodo AST no permitido '{type(node).__name__}'. Solo se admiten expresiones aritméticas puras."
                )

            if isinstance(node, ast.Name):
                if node.id.startswith("__") or node.id in {"eval", "exec", "open", "import", "compile", "globals", "locals"}:
                    raise SecurityViolationError(f"Identificador prohibido detectado: '{node.id}'")

            if isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_MATH_FUNCTIONS:
                    func_name = getattr(node.func, "id", str(node.func))
                    raise SecurityViolationError(
                        f"Llamada a función no permitida '{func_name}'. Permitidas: {list(ALLOWED_MATH_FUNCTIONS.keys())}"
                    )

        return tree

    def evaluate_safely(
        self,
        tree: ast.Expression,
        context: dict[str, float],
    ) -> float:
        """Evalúa el AST de manera segura en un entorno aislado sin builtins."""
        compiled = compile(tree, filename="<parametric_equation>", mode="eval")
        env: dict[str, Any] = {"__builtins__": {}}
        env.update(ALLOWED_MATH_FUNCTIONS)
        env.update(context)

        try:
            result = eval(compiled, env)
            if not isinstance(result, (int, float)):
                raise ValueError(f"El resultado debe ser numérico, recibido: {type(result)}")
            if math.isnan(result) or math.isinf(result):
                raise ValueError("El resultado evaluado divergió a NaN o Infinito")
            return float(result)
        except ZeroDivisionError as e:
            raise ValueError(f"División por cero en el punto {context}") from e
        except Exception as e:
            raise ValueError(f"Error evaluando ecuación con contexto {context}: {e}") from e

    def verify(self, spec: ParametricEquationSpec) -> VerificationReport:
        """Ejecuta la batería integral de pruebas de propiedades numéricas sobre la especificación."""
        tree = self.validate_ast_safety(spec.expression)
        failures: list[str] = []
        tests_run = 0
        tests_passed = 0

        # Verificar presencia de variables
        primary_var = spec.input_vars[0] if spec.input_vars else "x"
        bounds = spec.domain_bounds.get(primary_var, [0.0, 1.0])
        min_x, max_x = bounds[0], bounds[1]
        range_min, range_max = spec.range_bounds[0], spec.range_bounds[1]

        # 1. Prueba de Casos Límite y Singularidades
        tests_run += 1
        singularity_free = True
        critical_points = [
            min_x,
            max_x,
            (min_x + max_x) / 2.0,
            min_x + 1e-5 if min_x >= 0 else min_x,
            max_x - 1e-5 if max_x > min_x else max_x,
        ]
        if min_x <= 0.0 <= max_x:
            critical_points.append(0.0)

        for pt in critical_points:
            ctx = dict(spec.parameters)
            ctx[primary_var] = pt
            for other_var in spec.input_vars[1:]:
                other_bounds = spec.domain_bounds.get(other_var, [0.0, 1.0])
                ctx[other_var] = (other_bounds[0] + other_bounds[1]) / 2.0
            try:
                val = self.evaluate_safely(tree, ctx)
                if math.isnan(val) or math.isinf(val):
                    singularity_free = False
                    failures.append(f"Singularidad (NaN/Inf) en {primary_var}={pt}")
            except Exception as e:
                singularity_free = False
                failures.append(f"Excepción en punto crítico {primary_var}={pt}: {e}")
                break

        if singularity_free:
            tests_passed += 1

        # 2. Prueba de Dominio y Rango en Muestreo
        tests_run += 1
        domain_bounds_satisfied = True
        sample_points: list[dict[str, float]] = []

        step = (max_x - min_x) / max(1, self.num_samples - 1)
        sampled_y_values: list[float] = []

        for i in range(self.num_samples):
            x_val = min_x + i * step
            ctx = dict(spec.parameters)
            ctx[primary_var] = x_val
            for other_var in spec.input_vars[1:]:
                other_bounds = spec.domain_bounds.get(other_var, [0.0, 1.0])
                ctx[other_var] = (other_bounds[0] + other_bounds[1]) / 2.0

            try:
                y_val = self.evaluate_safely(tree, ctx)
                sample_points.append({primary_var: round(x_val, 4), spec.output_var: round(y_val, 4)})
                sampled_y_values.append(y_val)

                if y_val < (range_min - self.tolerance) or y_val > (range_max + self.tolerance):
                    domain_bounds_satisfied = False
                    failures.append(
                        f"Rango violado en {primary_var}={x_val:.3f}: valor={y_val:.4f} fuera de [{range_min}, {range_max}]"
                    )
                    break
            except Exception as e:
                domain_bounds_satisfied = False
                failures.append(f"Fallo durante muestreo en {primary_var}={x_val:.3f}: {e}")
                break

        if domain_bounds_satisfied:
            tests_passed += 1

        # 3. Prueba de Monotonía
        tests_run += 1
        monotonicity_satisfied = True
        if spec.monotonicity != "any" and len(sampled_y_values) >= 2:
            for i in range(len(sampled_y_values) - 1):
                y1 = sampled_y_values[i]
                y2 = sampled_y_values[i + 1]
                diff = y2 - y1

                if spec.monotonicity == "increasing" and diff < -self.tolerance:
                    monotonicity_satisfied = False
                    failures.append(f"Violación de monotonía creciente en paso {i}: y1={y1:.4f}, y2={y2:.4f}")
                    break
                elif spec.monotonicity == "decreasing" and diff > self.tolerance:
                    monotonicity_satisfied = False
                    failures.append(f"Violación de monotonía decreciente en paso {i}: y1={y1:.4f}, y2={y2:.4f}")
                    break
                elif spec.monotonicity == "constant" and abs(diff) > self.tolerance:
                    monotonicity_satisfied = False
                    failures.append(f"Violación de función constante en paso {i}: y1={y1:.4f}, y2={y2:.4f}")
                    break

        if monotonicity_satisfied:
            tests_passed += 1

        # Formato de fórmula en LaTeX para visualización
        latex_formula = spec.latex_repr or self._generate_basic_latex(spec.expression, spec.output_var)

        is_valid = (
            singularity_free
            and domain_bounds_satisfied
            and monotonicity_satisfied
            and len(failures) == 0
        )

        return VerificationReport(
            equation_id=spec.equation_id,
            is_valid=is_valid,
            tests_run=tests_run,
            tests_passed=tests_passed,
            monotonicity_satisfied=monotonicity_satisfied,
            domain_bounds_satisfied=domain_bounds_satisfied,
            singularity_free=singularity_free,
            failure_reasons=failures,
            sample_points=sample_points[:25],  # Muestra representativa para UI
            latex_formula=latex_formula,
        )

    def _generate_basic_latex(self, expression: str, output_var: str) -> str:
        """Genera una representación básica en LaTeX a partir de la expresión matemática."""
        clean = expression.replace("*", r" \cdot ")
        clean = clean.replace("exp(", "e^{").replace("sqrt(", r"\sqrt{")
        return f"{output_var} = {clean}"
