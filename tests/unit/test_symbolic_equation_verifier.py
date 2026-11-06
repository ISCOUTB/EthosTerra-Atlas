from __future__ import annotations

import pytest

from src.domain.v2.institutional_schemas import ParametricEquationSpec
from src.application.symbolic_equation_verifier import (
    SymbolicEquationVerifier,
    SecurityViolationError,
)


def test_ast_safety_allows_valid_math():
    verifier = SymbolicEquationVerifier()
    # Expresiones matemáticas puras válidas
    assert verifier.validate_ast_safety("r_base * (1.0 - delta * social_capital)") is not None
    assert verifier.validate_ast_safety("a * exp(-b * x) + sqrt(y)") is not None
    assert verifier.validate_ast_safety("min(x, 10.0) + max(y, 0.0)") is not None


@pytest.mark.parametrize("malicious_expr", [
    "__import__('os').system('ls')",
    "eval('1+1')",
    "open('/etc/passwd').read()",
    "x.__class__.__bases__",
    "exec('import sys')",
    "[x for x in (1, 2)]",
    "lambda x: x + 1",
])
def test_ast_safety_blocks_malicious_code(malicious_expr: str):
    verifier = SymbolicEquationVerifier()
    with pytest.raises(SecurityViolationError):
        verifier.validate_ast_safety(malicious_expr)


def test_verify_linear_decreasing_equation_success():
    verifier = SymbolicEquationVerifier(num_samples=50)
    spec = ParametricEquationSpec(
        equation_id="tasa_credito_asociatividad",
        expression="r_base * (1.0 - delta * social_capital)",
        input_vars=["social_capital"],
        output_var="tasa_interes",
        parameters={"r_base": 0.12, "delta": 0.3},
        domain_bounds={"social_capital": [0.0, 1.0]},
        range_bounds=[0.05, 0.15],
        monotonicity="decreasing",
        description="Alivio de tasa de crédito según asociatividad campesina",
    )
    report = verifier.verify(spec)
    assert report.is_valid is True
    assert report.monotonicity_satisfied is True
    assert report.domain_bounds_satisfied is True
    assert report.singularity_free is True
    assert report.tests_passed == report.tests_run
    assert len(report.sample_points) > 0
    assert "tasa_interes" in report.latex_formula


def test_verify_detects_monotonicity_violation():
    verifier = SymbolicEquationVerifier(num_samples=50)
    # Parábola con mínimo en x=0.5: no es decreciente en todo [0, 1]
    spec = ParametricEquationSpec(
        equation_id="curva_parabolica_invalida",
        expression="(x - 0.5) ** 2 + 0.1",
        input_vars=["x"],
        output_var="y",
        parameters={},
        domain_bounds={"x": [0.0, 1.0]},
        range_bounds=[0.0, 1.0],
        monotonicity="decreasing",
    )
    report = verifier.verify(spec)
    assert report.is_valid is False
    assert report.monotonicity_satisfied is False
    assert any("monotonía" in f for f in report.failure_reasons)


def test_verify_detects_range_violation():
    verifier = SymbolicEquationVerifier(num_samples=50)
    # Excede el límite superior de 1.0
    spec = ParametricEquationSpec(
        equation_id="exceso_de_rango",
        expression="x * 2.0",
        input_vars=["x"],
        output_var="y",
        parameters={},
        domain_bounds={"x": [0.0, 1.0]},
        range_bounds=[0.0, 1.0],
        monotonicity="increasing",
    )
    report = verifier.verify(spec)
    assert report.is_valid is False
    assert report.domain_bounds_satisfied is False
    assert any("Rango violado" in f for f in report.failure_reasons)


def test_verify_detects_singularity_division_by_zero():
    verifier = SymbolicEquationVerifier(num_samples=50)
    # x=0 en el dominio provoca división por cero
    spec = ParametricEquationSpec(
        equation_id="singularidad_cero",
        expression="10.0 / x",
        input_vars=["x"],
        output_var="y",
        parameters={},
        domain_bounds={"x": [0.0, 5.0]},
        range_bounds=[0.0, 100.0],
        monotonicity="decreasing",
    )
    report = verifier.verify(spec)
    assert report.is_valid is False
    assert report.singularity_free is False
    assert any("Excepción en punto crítico" in f or "Singularidad" in f for f in report.failure_reasons)


def test_verify_exponential_saturation_success():
    verifier = SymbolicEquationVerifier(num_samples=50)
    spec = ParametricEquationSpec(
        equation_id="subsidio_saturacion",
        expression="max_subsidy * (1.0 - exp(-k * area))",
        input_vars=["area"],
        output_var="subsidio",
        parameters={"max_subsidy": 1000000.0, "k": 0.5},
        domain_bounds={"area": [0.0, 10.0]},
        range_bounds=[0.0, 1000000.0],
        monotonicity="increasing",
    )
    report = verifier.verify(spec)
    assert report.is_valid is True
    assert report.monotonicity_satisfied is True
    assert report.domain_bounds_satisfied is True
