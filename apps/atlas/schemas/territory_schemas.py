from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class PolicyInstrumentRef(BaseModel):
    """Referencia a un instrumento formal de política pública aplicable."""
    model_config = ConfigDict(extra="forbid", strict=True)

    instrument_id: str = Field(..., description="Identificador único del instrumento")
    name: str = Field(..., description="Nombre formal del instrumento")
    level: Literal["nacional", "subregional_pdet", "departamental", "municipal"] = Field(
        ..., description="Nivel territorial de emisión"
    )
    issuing_entity: str = Field(..., description="Entidad gubernamental que emite el instrumento")
    adoption_norm: str = Field(..., description="Norma de adopción oficial (Ley, Ordenanza, Acuerdo, Resolución)")
    validity_start_year: int = Field(..., ge=1990, le=2050, description="Año inicial de vigencia")
    validity_end_year: int | None = Field(default=None, ge=1990, le=2050, description="Año final de vigencia si aplica")
    canonical_url: str | None = Field(default=None, description="URL canónica oficial de consulta")


class TerritoryHierarchy(BaseModel):
    """Jerarquía territorial completa desde nivel municipal hasta nivel nación."""
    model_config = ConfigDict(extra="forbid", strict=True)

    # Nivel Municipal
    municipality_code: str = Field(..., pattern=r"^\d{5}$", description="Código DIVIPOLA de 5 dígitos del municipio")
    municipality_name: str = Field(..., description="Nombre del municipio")

    # Nivel Subregional PDET
    pdet_subregion_code: str | None = Field(default=None, description="Código de la subregión PDET si aplica")
    pdet_subregion_name: str | None = Field(default=None, description="Nombre de la subregión PDET")
    is_pdet: bool = Field(..., description="Indica si el municipio hace parte de una subregión PDET")

    # Nivel Departamental
    department_code: str = Field(..., pattern=r"^\d{2}$", description="Código DIVIPOLA de 2 dígitos del departamento")
    department_name: str = Field(..., description="Nombre del departamento")

    # Nivel Nacional
    country_code: str = Field(default="CO", description="Código ISO del país")
    country_name: str = Field(default="Colombia", description="Nombre del país")

    # Instrumentos aplicables en cascada
    applicable_instruments: list[PolicyInstrumentRef] = Field(
        default_factory=list, description="Lista de instrumentos aplicables a este territorio"
    )

    # Metadatos del resolvedor
    data_source: str = Field(default="DANE_MGN_2024", description="Fuente de referencia geoestadística")
