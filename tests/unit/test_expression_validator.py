from __future__ import annotations

import pytest
from src.application.expression_validator import validate_activation_when


def test_validate_activation_when_valid_expression():
    expr = "state.hasLandWithSeason('NONE') || state.hasLandWithSeason('FALLOW')"
    res = validate_activation_when(expr)
    assert res.syntax_valid is True
    assert res.runtime_compatible == "unknown"
    assert res.requires_simulation_test is True
    assert "hasLandWithSeason" in res.detected_methods
    assert "||" in res.detected_operators


def test_validate_activation_when_empty_expression():
    res = validate_activation_when("   ")
    assert res.syntax_valid is False
    assert res.runtime_compatible == "no"


def test_validate_activation_when_unbalanced_parentheses():
    res = validate_activation_when("state.hasLandWithSeason('NONE'")
    assert res.syntax_valid is False
    assert any("Paréntesis desbalanceados" in e for e in res.syntax_errors)


def test_validate_activation_when_unbalanced_quotes():
    res = validate_activation_when("state.hasLandWithSeason('NONE)")
    assert res.syntax_valid is False
    assert any("Comillas desbalanceadas" in e for e in res.syntax_errors)
