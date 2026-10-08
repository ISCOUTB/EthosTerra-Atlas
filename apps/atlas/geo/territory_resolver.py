from __future__ import annotations

from typing import Any
from apps.atlas.schemas.territory_schemas import PolicyInstrumentRef, TerritoryHierarchy


# Base de datos de municipios de Montes de María (15 municipios oficiales) y Bolívar
MONTES_DE_MARIA_MUNICIPALITIES: dict[str, dict[str, Any]] = {
    # Bolívar (8 municipios en Montes de María)
    "13244": {
        "name": "El Carmen de Bolívar",
        "department_code": "13",
        "department_name": "Bolívar",
        "is_pdet": True,
        "pdet_code": "PDET_01",
        "pdet_name": "Montes de María",
        "pdt_name": "Plan de Desarrollo Municipal de El Carmen de Bolívar",
        "pdt_norm": "Acuerdo Municipal 004 de 2024",
    },
    "13654": {
        "name": "San Jacinto",
        "department_code": "13",
        "department_name": "Bolívar",
        "is_pdet": True,
        "pdet_code": "PDET_01",
        "pdet_name": "Montes de María",
        "pdt_name": "Plan de Desarrollo Municipal de San Jacinto",
        "pdt_norm": "Acuerdo Municipal 006 de 2024",
    },
    "13657": {
        "name": "San Juan Nepomuceno",
        "department_code": "13",
        "department_name": "Bolívar",
        "is_pdet": True,
        "pdet_code": "PDET_01",
        "pdet_name": "Montes de María",
        "pdt_name": "Plan de Desarrollo Municipal de San Juan Nepomuceno",
        "pdt_norm": "Acuerdo Municipal 005 de 2024",
    },
    "13442": {
        "name": "María La Baja",
        "department_code": "13",
        "department_name": "Bolívar",
        "is_pdet": True,
        "pdet_code": "PDET_01",
        "pdet_name": "Montes de María",
        "pdt_name": "Plan de Desarrollo Municipal de María La Baja",
        "pdt_norm": "Acuerdo Municipal 007 de 2024",
    },
    "13212": {
        "name": "Córdoba Tetón",
        "department_code": "13",
        "department_name": "Bolívar",
        "is_pdet": True,
        "pdet_code": "PDET_01",
        "pdet_name": "Montes de María",
        "pdt_name": "Plan de Desarrollo Municipal de Córdoba",
        "pdt_norm": "Acuerdo Municipal 003 de 2024",
    },
    "13248": {
        "name": "El Guamo",
        "department_code": "13",
        "department_name": "Bolívar",
        "is_pdet": True,
        "pdet_code": "PDET_01",
        "pdet_name": "Montes de María",
        "pdt_name": "Plan de Desarrollo Municipal de El Guamo",
        "pdt_norm": "Acuerdo Municipal 005 de 2024",
    },
    "13894": {
        "name": "Zambrano",
        "department_code": "13",
        "department_name": "Bolívar",
        "is_pdet": True,
        "pdet_code": "PDET_01",
        "pdet_name": "Montes de María",
        "pdt_name": "Plan de Desarrollo Municipal de Zambrano",
        "pdt_norm": "Acuerdo Municipal 004 de 2024",
    },
    "13667": {
        "name": "San Pablo Norte (Montes de María)",
        "department_code": "13",
        "department_name": "Bolívar",
        "is_pdet": True,
        "pdet_code": "PDET_01",
        "pdet_name": "Montes de María",
        "pdt_name": "Plan de Desarrollo Territorial Sectorial",
        "pdt_norm": "Acuerdo Municipal 002 de 2024",
    },
    # Sucre (7 municipios en Montes de María - Caso Multi-departamental)
    "70717": {
        "name": "San Onofre",
        "department_code": "70",
        "department_name": "Sucre",
        "is_pdet": True,
        "pdet_code": "PDET_01",
        "pdet_name": "Montes de María",
        "pdt_name": "Plan de Desarrollo Municipal de San Onofre",
        "pdt_norm": "Acuerdo Municipal 008 de 2024",
    },
    "70508": {
        "name": "Ovejas",
        "department_code": "70",
        "department_name": "Sucre",
        "is_pdet": True,
        "pdet_code": "PDET_01",
        "pdet_name": "Montes de María",
        "pdt_name": "Plan de Desarrollo Municipal de Ovejas",
        "pdt_norm": "Acuerdo Municipal 005 de 2024",
    },
    "70230": {
        "name": "Chalán",
        "department_code": "70",
        "department_name": "Sucre",
        "is_pdet": True,
        "pdet_code": "PDET_01",
        "pdet_name": "Montes de María",
        "pdt_name": "Plan de Desarrollo Municipal de Chalán",
        "pdt_norm": "Acuerdo Municipal 003 de 2024",
    },
    "70204": {
        "name": "Colosó",
        "department_code": "70",
        "department_name": "Sucre",
        "is_pdet": True,
        "pdet_code": "PDET_01",
        "pdet_name": "Montes de María",
        "pdt_name": "Plan de Desarrollo Municipal de Colosó",
        "pdt_norm": "Acuerdo Municipal 004 de 2024",
    },
    "70418": {
        "name": "Los Palmitos",
        "department_code": "70",
        "department_name": "Sucre",
        "is_pdet": True,
        "pdet_code": "PDET_01",
        "pdet_name": "Montes de María",
        "pdt_name": "Plan de Desarrollo Municipal de Los Palmitos",
        "pdt_norm": "Acuerdo Municipal 006 de 2024",
    },
    "70473": {
        "name": "Morroa",
        "department_code": "70",
        "department_name": "Sucre",
        "is_pdet": True,
        "pdet_code": "PDET_01",
        "pdet_name": "Montes de María",
        "pdt_name": "Plan de Desarrollo Municipal de Morroa",
        "pdt_norm": "Acuerdo Municipal 005 de 2024",
    },
    "70823": {
        "name": "Toluviejo",
        "department_code": "70",
        "department_name": "Sucre",
        "is_pdet": True,
        "pdet_code": "PDET_01",
        "pdet_name": "Montes de María",
        "pdt_name": "Plan de Desarrollo Municipal de Toluviejo",
        "pdt_norm": "Acuerdo Municipal 007 de 2024",
    },
    "70523": {
        "name": "San Antonio de Palmito",
        "department_code": "70",
        "department_name": "Sucre",
        "is_pdet": True,
        "pdet_code": "PDET_01",
        "pdet_name": "Montes de María",
        "pdt_name": "Plan de Desarrollo Municipal de San Antonio de Palmito",
        "pdt_norm": "Acuerdo Municipal 004 de 2024",
    },
}

# Instrumentos Nivel Nacional
INSTRUMENT_NACION = PolicyInstrumentRef(
    instrument_id="PND_COL_2022_2026",
    name="Plan Nacional de Desarrollo: Colombia Potencia Mundial de la Vida",
    level="nacional",
    issuing_entity="Departamento Nacional de Planeación (DNP)",
    adoption_norm="Ley 2294 de 2023",
    validity_start_year=2022,
    validity_end_year=2026,
    canonical_url="https://colaboracion.dnp.gov.co/CDI/PND/2022-2026/PND_2022-2026.pdf",
)

# Instrumento Nivel Subregional PDET
INSTRUMENT_PDET_MONTES_DE_MARIA = PolicyInstrumentRef(
    instrument_id="PATR_PDET_MONTES_DE_MARIA",
    name="Plan de Acción para la Transformación Regional (PATR) - Montes de María",
    level="subregional_pdet",
    issuing_entity="Agencia de Renovación del Territorio (ART)",
    adoption_norm="Decreto Ley 893 de 2017",
    validity_start_year=2018,
    validity_end_year=2028,
    canonical_url="https://www.renovacionterritorio.gov.co/descargar.php?idFile=22158",
)

# Instrumentos Nivel Departamental (Bolívar vs Sucre)
INSTRUMENT_PIDARET_BOLIVAR = PolicyInstrumentRef(
    instrument_id="PIDARET_BOLIVAR_2021_2040",
    name="Plan Integral de Desarrollo Agropecuario y Rural con Enfoque Territorial (PIDARET) Bolívar",
    level="departamental",
    issuing_entity="Agencia de Desarrollo Rural (ADR) / UPRA / Asamblea Departamental de Bolívar",
    adoption_norm="Ordenanza 323 de 2021",
    validity_start_year=2021,
    validity_end_year=2040,
    canonical_url="https://www.adr.gov.co/wp-content/uploads/2021/08/PIDARET-Bolivar-2021.pdf",
)

INSTRUMENT_PIDARET_SUCRE = PolicyInstrumentRef(
    instrument_id="PIDARET_SUCRE_2020_2039",
    name="Plan Integral de Desarrollo Agropecuario y Rural con Enfoque Territorial (PIDARET) Sucre",
    level="departamental",
    issuing_entity="Agencia de Desarrollo Rural (ADR) / UPRA / Asamblea Departamental de Sucre",
    adoption_norm="Ordenanza 011 de 2020",
    validity_start_year=2020,
    validity_end_year=2039,
    canonical_url="https://www.adr.gov.co/wp-content/uploads/2021/04/PIDARET-Sucre.pdf",
)


class TerritoryResolver:
    """Motor determinista de resolución territorial jerárquica bajo códigos DIVIPOLA."""

    def __init__(self, custom_data: dict[str, dict[str, Any]] | None = None) -> None:
        self.catalog = custom_data if custom_data is not None else MONTES_DE_MARIA_MUNICIPALITIES

    def resolve_by_divipola(self, municipality_code: str) -> TerritoryHierarchy:
        """Resuelve la jerarquía completa e instrumentos aplicables a partir de un código DIVIPOLA de 5 dígitos."""
        code = str(municipality_code).strip()
        if code not in self.catalog:
            raise KeyError(
                f"Código DIVIPOLA '{code}' no encontrado en el catálogo territorial del atlas. "
                f"Municipios disponibles: {list(self.catalog.keys())}"
            )

        data = self.catalog[code]
        dept_code = data["department_code"]

        # 1. Cascada de instrumentos
        instruments: list[PolicyInstrumentRef] = [INSTRUMENT_NACION]

        # 2. Nivel Subregional PDET
        if data.get("is_pdet"):
            instruments.append(INSTRUMENT_PDET_MONTES_DE_MARIA)

        # 3. Nivel Departamental (Bolívar usa Ordenanza 323 de 2021; Sucre usa Ordenanza 011 de 2020)
        if dept_code == "13":
            instruments.append(INSTRUMENT_PIDARET_BOLIVAR)
        elif dept_code == "70":
            instruments.append(INSTRUMENT_PIDARET_SUCRE)

        # 4. Nivel Municipal
        municipal_instrument = PolicyInstrumentRef(
            instrument_id=f"PDT_{code}",
            name=data["pdt_name"],
            level="municipal",
            issuing_entity=f"Alcaldía Municipal de {data['name']} / Concejo Municipal",
            adoption_norm=data["pdt_norm"],
            validity_start_year=2024,
            validity_end_year=2027,
            canonical_url=None,
        )
        instruments.append(municipal_instrument)

        return TerritoryHierarchy(
            municipality_code=code,
            municipality_name=data["name"],
            pdet_subregion_code=data.get("pdet_code"),
            pdet_subregion_name=data.get("pdet_name"),
            is_pdet=bool(data.get("is_pdet")),
            department_code=dept_code,
            department_name=data["department_name"],
            country_code="CO",
            country_name="Colombia",
            applicable_instruments=instruments,
            data_source="DANE_MGN_2024",
        )

    def list_montes_de_maria_pilots(self) -> list[str]:
        """Devuelve los códigos DIVIPOLA de los 5 casos piloto obligatorios."""
        return [
            "13244",  # El Carmen de Bolívar
            "13654",  # San Jacinto
            "13657",  # San Juan Nepomuceno
            "13442",  # María La Baja
            "70717",  # San Onofre (Sucre - Piloto multi-departamental)
        ]

    def list_all_montes_de_maria_municipalities(self) -> list[str]:
        """Devuelve los 15 códigos DIVIPOLA oficiales de la subregión PDET Montes de María."""
        return [
            "13212",  # Córdoba Tetón
            "13244",  # El Carmen de Bolívar
            "13248",  # El Guamo
            "13442",  # María La Baja
            "13654",  # San Jacinto
            "13657",  # San Juan Nepomuceno
            "13894",  # Zambrano
            "70204",  # Colosó
            "70230",  # Chalán
            "70418",  # Los Palmitos
            "70473",  # Morroa
            "70508",  # Ovejas
            "70523",  # San Antonio de Palmito
            "70717",  # San Onofre
            "70823",  # Toluviejo
        ]
