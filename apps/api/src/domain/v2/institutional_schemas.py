from __future__ import annotations

import re
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

KnowledgeTier = Literal["peasant_narrative", "spatial_restriction", "institutional_policy"]
PolicyDomain = Literal["credit_bank", "market_pricing", "civic_subsidies", "water_quota", "agro_extension"]
TargetInstitution = Literal["BankOffice", "MarketPlace", "CivicAuthority", "AgroEcosystem", "CommunityDynamics"]
MonotonicityType = Literal["increasing", "decreasing", "constant", "any"]


class ParametricEquationSpec(BaseModel):
    """Especificación declarativa de una función o relación matemática institucional."""
    model_config = ConfigDict(extra="forbid")

    equation_id: str = Field(..., description="Identificador único en formato snake_case")
    expression: str = Field(..., description="Expresión matemática evaluable segura (ej: 'r_base * (1.0 - delta * social_capital)')")
    input_vars: list[str] = Field(..., description="Lista de variables de entrada requeridas")
    output_var: str = Field(..., description="Variable del simulador que recibe el valor calculado")
    parameters: dict[str, float] = Field(default_factory=dict, description="Constantes y coeficientes de la ecuación")
    domain_bounds: dict[str, list[float]] = Field(
        ...,
        description="Rango válido de cada variable de entrada [min, max]",
    )
    range_bounds: list[float] = Field(
        ...,
        description="Rango estricto [min, max] en el que debe confinarse la salida calculada",
    )
    monotonicity: MonotonicityType = Field(default="any", description="Propiedad de monotonía esperada")
    latex_repr: str | None = Field(default=None, description="Representación matemática en LaTeX para la UI")
    description: str = Field(default="", description="Explicación agronómica o institucional de la relación")

    @field_validator("equation_id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not re.match(r"^[a-z][a-z0-9_]*$", v):
            raise ValueError(f"equation_id '{v}' debe cumplir con formato snake_case ^[a-z][a-z0-9_]*$")
        return v

    @field_validator("domain_bounds")
    @classmethod
    def validate_domain_bounds(cls, v: dict[str, list[float]]) -> dict[str, list[float]]:
        for var, bounds in v.items():
            if len(bounds) != 2 or bounds[0] > bounds[1]:
                raise ValueError(f"domain_bounds para '{var}' debe ser una lista [min, max] con min <= max")
        return v

    @field_validator("range_bounds")
    @classmethod
    def validate_range_bounds(cls, v: list[float]) -> list[float]:
        if len(v) != 2 or v[0] > v[1]:
            raise ValueError("range_bounds debe ser una lista [min, max] con min <= max")
        return v


class VerificationReport(BaseModel):
    """Reporte formal de la batería de pruebas de propiedades numéricas de una ecuación."""
    model_config = ConfigDict(extra="forbid")

    equation_id: str
    is_valid: bool
    tests_run: int
    tests_passed: int
    monotonicity_satisfied: bool
    domain_bounds_satisfied: bool
    singularity_free: bool
    failure_reasons: list[str] = Field(default_factory=list)
    sample_points: list[dict[str, float]] = Field(
        default_factory=list,
        description="Puntos muestreados (x, y) para renderizado gráfico en la interfaz de curaduría",
    )
    latex_formula: str


class InstitutionalPolicySpec(BaseModel):
    """Especificación declarativa ejecutable de una política institucional (Semana 11 - B7)."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Identificador único en formato snake_case")
    version: str = Field(default="1.0", description="Versión del contrato")
    display_name: str = Field(..., min_length=3, max_length=150)
    description: str = Field(..., min_length=10)
    knowledge_tier: KnowledgeTier = Field(default="institutional_policy")
    policy_domain: PolicyDomain = Field(..., description="Dominio de política")
    target_institution: TargetInstitution = Field(..., description="Agente de EthosTerra que adopta la regla")
    activation_condition: str | None = Field(default=None, description="Condición simpleeval para activar la política")
    equations: list[ParametricEquationSpec] = Field(default_factory=list, description="Relaciones funcionales verificadas")
    static_parameters: dict[str, Any] = Field(default_factory=dict, description="Parámetros estáticos de la institución")
    normative_tags: list[str] = Field(default_factory=list, description="Etiquetas de trazabilidad normativa")
    document_source_id: str = Field(..., description="Identificador del documento fuente")
    document_source_hash: str = Field(..., description="Hash SHA-256 del documento fuente")

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        if not re.match(r"^[a-z][a-z0-9_]*$", v):
            raise ValueError(f"id '{v}' debe cumplir con formato snake_case ^[a-z][a-z0-9_]*$")
        return v
