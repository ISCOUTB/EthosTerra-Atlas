import json
from pathlib import Path
import sys
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.atlas.geo.territory_resolver import TerritoryResolver
from apps.atlas.schemas.territory_schemas import TerritoryHierarchy


@pytest.fixture
def resolver() -> TerritoryResolver:
    return TerritoryResolver()


def test_resolver_five_required_pilots(resolver: TerritoryResolver):
    pilots = resolver.list_montes_de_maria_pilots()
    assert len(pilots) == 5
    assert pilots == ["13244", "13654", "13657", "13442", "70717"]


def test_el_carmen_de_bolivar_hierarchy_and_instruments(resolver: TerritoryResolver):
    res = resolver.resolve_by_divipola("13244")
    assert isinstance(res, TerritoryHierarchy)
    assert res.municipality_name == "El Carmen de Bolívar"
    assert res.department_code == "13"
    assert res.department_name == "Bolívar"
    assert res.is_pdet is True
    assert res.pdet_subregion_name == "Montes de María"

    # Verificar que el PIDARET de Bolívar use la Ordenanza 323 de 2021
    pidaret = next(i for i in res.applicable_instruments if i.level == "departamental")
    assert pidaret.instrument_id == "PIDARET_BOLIVAR_2021_2040"
    assert "Ordenanza 323 de 2021" in pidaret.adoption_norm

    # Verificar que incluya PATR Montes de María y PND
    levels = {i.level for i in res.applicable_instruments}
    assert levels == {"nacional", "subregional_pdet", "departamental", "municipal"}


def test_san_jacinto_hierarchy(resolver: TerritoryResolver):
    res = resolver.resolve_by_divipola("13654")
    assert res.municipality_name == "San Jacinto"
    assert res.department_code == "13"
    assert any("Ordenanza 323 de 2021" in i.adoption_norm for i in res.applicable_instruments)


def test_san_juan_nepomuceno_hierarchy(resolver: TerritoryResolver):
    res = resolver.resolve_by_divipola("13657")
    assert res.municipality_name == "San Juan Nepomuceno"
    assert res.department_code == "13"
    assert any("Ordenanza 323 de 2021" in i.adoption_norm for i in res.applicable_instruments)


def test_maria_la_baja_hierarchy(resolver: TerritoryResolver):
    res = resolver.resolve_by_divipola("13442")
    assert res.municipality_name == "María La Baja"
    assert res.department_code == "13"
    assert any("Ordenanza 323 de 2021" in i.adoption_norm for i in res.applicable_instruments)


def test_san_onofre_sucre_multidepartmental_case(resolver: TerritoryResolver):
    # Piloto 5 determinista de Sucre
    res = resolver.resolve_by_divipola("70717")
    assert res.municipality_name == "San Onofre"
    assert res.department_code == "70"
    assert res.department_name == "Sucre"
    assert res.is_pdet is True
    assert res.pdet_subregion_name == "Montes de María"

    # En Sucre no debe aplicar la Ordenanza de Bolívar, sino PIDARET Sucre
    dept_inst = next(i for i in res.applicable_instruments if i.level == "departamental")
    assert dept_inst.instrument_id == "PIDARET_SUCRE_2020_2039"
    assert "Sucre" in dept_inst.issuing_entity
    assert "Ordenanza 323 de 2021" not in dept_inst.adoption_norm

    # Pero sí debe compartir el mismo PATR de Montes de María
    pdet_inst = next(i for i in res.applicable_instruments if i.level == "subregional_pdet")
    assert pdet_inst.instrument_id == "PATR_PDET_MONTES_DE_MARIA"


def test_ovejas_sucre_optional_extended_case(resolver: TerritoryResolver):
    # Ovejas como caso extendido opcional
    res = resolver.resolve_by_divipola("70508")
    assert res.municipality_name == "Ovejas"
    assert res.department_code == "70"
    assert res.department_name == "Sucre"


def test_list_all_montes_de_maria_municipalities(resolver: TerritoryResolver):
    all_codes = resolver.list_all_montes_de_maria_municipalities()
    assert len(all_codes) == 15
    # 7 de Bolívar
    bolivar_codes = {"13212", "13244", "13248", "13442", "13654", "13657", "13894"}
    assert bolivar_codes.issubset(set(all_codes))
    # 8 de Sucre
    sucre_codes = {"70204", "70230", "70418", "70473", "70508", "70523", "70717", "70823"}
    assert sucre_codes.issubset(set(all_codes))


def test_resolve_san_antonio_de_palmito_sucre(resolver: TerritoryResolver):
    res = resolver.resolve_by_divipola("70523")
    assert res.municipality_name == "San Antonio de Palmito"
    assert res.department_code == "70"
    assert res.department_name == "Sucre"
    assert res.is_pdet is True
    assert any(i.instrument_id == "PIDARET_SUCRE_2020_2039" for i in res.applicable_instruments)
    assert any(i.instrument_id == "PATR_PDET_MONTES_DE_MARIA" for i in res.applicable_instruments)


def test_resolve_zambrano_bolivar(resolver: TerritoryResolver):
    res = resolver.resolve_by_divipola("13894")
    assert res.municipality_name == "Zambrano"
    assert res.department_code == "13"
    assert res.department_name == "Bolívar"
    assert res.is_pdet is True
    assert any(i.instrument_id == "PIDARET_BOLIVAR_2021_2040" for i in res.applicable_instruments)
    assert any(i.instrument_id == "PATR_PDET_MONTES_DE_MARIA" for i in res.applicable_instruments)


def test_unknown_divipola_raises_key_error(resolver: TerritoryResolver):
    with pytest.raises(KeyError) as exc_info:
        resolver.resolve_by_divipola("99999")
    assert "Código DIVIPOLA '99999' no encontrado" in str(exc_info.value)


def test_dane_geojson_file_integrity():
    geojson_path = Path("apps/atlas/geo/dane_mgn_montes_de_maria.geojson")
    assert geojson_path.exists()
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    assert data["type"] == "FeatureCollection"
    features = data["features"]
    assert len(features) >= 5

    divipolas = {f["properties"]["divipola"] for f in features}
    assert {"13244", "13654", "13657", "13442", "70717"}.issubset(divipolas)


def test_sources_registry_yaml_integrity():
    yaml_path = Path("apps/atlas/config/sources_registry.yaml")
    assert yaml_path.exists()
    content = yaml_path.read_text(encoding="utf-8")
    assert "Ordenanza 323 de 2021" in content
    assert "art_patr_montes_de_maria" in content
    assert "datos_gov_co_eva_agricola" in content
    assert "dane_mgn_limites_municipales" in content


def test_api_atlas_endpoints():
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)

    # 1. Listar territorios
    r_list = client.get("/v2/atlas/territories")
    assert r_list.status_code == 200
    data_list = r_list.json()
    assert "territories" in data_list
    assert data_list["pilots_count"] == 5

    # 2. Resolver Carmen de Bolívar (13244)
    r_carmen = client.get("/v2/atlas/territories/13244")
    assert r_carmen.status_code == 200
    data_carmen = r_carmen.json()
    assert data_carmen["municipality_name"] == "El Carmen de Bolívar"
    assert any("Ordenanza 323 de 2021" in i["adoption_norm"] for i in data_carmen["applicable_instruments"])

    # 3. Resolver San Onofre (70717 - Sucre)
    r_onofre = client.get("/v2/atlas/territories/70717")
    assert r_onofre.status_code == 200
    data_onofre = r_onofre.json()
    assert data_onofre["department_name"] == "Sucre"
    assert any("Sucre" in i["name"] for i in data_onofre["applicable_instruments"])

    # 4. GeoJSON
    r_geo = client.get("/v2/atlas/geojson")
    assert r_geo.status_code == 200
    assert r_geo.json()["type"] == "FeatureCollection"

    # 5. Fuentes YAML
    r_src = client.get("/v2/atlas/sources")
    assert r_src.status_code == 200
    assert "sources" in r_src.json()
