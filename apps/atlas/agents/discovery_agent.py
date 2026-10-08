from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from apps.atlas.geo.territory_resolver import TerritoryResolver
from apps.atlas.collectors.policy_verifier import PolicyVerifier
from apps.atlas.schemas.discovery_schemas import (
    CandidateSourceRecord,
    ConfidenceLevel,
    DiscoveryQuery,
    DiscoveryResult,
    DiscoveryStatus,
    InstrumentType,
)

# Lista blanca estricta de dominios institucionales autorizados (Soberanía y Oficialidad)
OFFICIAL_DOMAIN_SUFFIXES = (
    ".gov.co",
    "gov.co",
    "renovacionterritorio.gov.co",
    "adr.gov.co",
    "dane.gov.co",
    "dnp.gov.co",
    "upra.gov.co",
    "datos.gov.co",
    "bolivar.gov.co",
    "sucre.gov.co",
)

# Mapeo determinista de fuentes registradas a tipos de instrumentos
SOURCE_TO_INSTRUMENTS: dict[str, list[InstrumentType]] = {
    "art_patr_montes_de_maria": ["PATR"],
    "adr_pidaret_bolivar_ordenanza_323_2021": ["PIDARET", "ordenanza"],
    "adr_pidaret_sucre_ordenanza": ["PIDARET", "ordenanza"],
    "pnd_colombia_2022_2026": ["PDT"],
    "datos_gov_co_eva_agricola": ["datos_agricolas"],
    "dane_mgn_limites_municipales": ["datos_agricolas"],
}


class DiscoveryAgentError(Exception):
    """Error base en el agente de descubrimiento documental."""
    pass


class DocumentDiscoveryAgent:
    """Agente local de descubrimiento documental territorial.

    Responsabilidad estricta: Descubrir, correlacionar y priorizar fuentes oficiales aplicables
    a un territorio sin descargar contenidos ni emitir aprobaciones automáticas.
    """

    def __init__(
        self,
        resolver: TerritoryResolver | None = None,
        verifier: PolicyVerifier | None = None,
        url_probe_fn: Callable[[str], dict[str, Any]] | None = None,
    ) -> None:
        self.resolver = resolver or TerritoryResolver()
        self.verifier = verifier or PolicyVerifier()
        self._url_probe_fn = url_probe_fn

    @staticmethod
    def is_official_domain(url: str) -> bool:
        """Verifica deterministamente si la URL pertenece a un dominio gubernamental autorizado."""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
            hostname = hostname.lower()
            return any(
                hostname == suffix or hostname.endswith("." + suffix.lstrip("."))
                for suffix in OFFICIAL_DOMAIN_SUFFIXES
            )
        except Exception:
            return False

    def discover_sources(self, query: DiscoveryQuery) -> DiscoveryResult:
        """Ejecuta el descubrimiento determinista para la consulta territorial."""
        # 1. Resolver jerarquía territorial formal reutilizando TerritoryResolver
        try:
            hierarchy = self.resolver.resolve_by_divipola(query.divipola)
        except KeyError as e:
            raise DiscoveryAgentError(f"Código DIVIPOLA '{query.divipola}' no reconocido por el resolvedor.") from e

        now_iso = datetime.now(timezone.utc).isoformat()
        candidates: list[CandidateSourceRecord] = []
        seen_urls: set[str] = set()

        # Determinar alcances territoriales aplicables según jerarquía
        applicable_scopes: set[str] = {"COLOMBIA", "NACIONAL", "NACIONAL_POR_DIVIPOLA"}
        if hierarchy.is_pdet:
            applicable_scopes.update({
                "PDET_01",
                "PDET_01_MONTES_DE_MARIA",
                "MONTES_DE_MARIA",
            })
            if hierarchy.pdet_subregion_code:
                applicable_scopes.add(hierarchy.pdet_subregion_code)
                applicable_scopes.add(f"{hierarchy.pdet_subregion_code}_MONTES_DE_MARIA")

        # Departamento específico (Bolívar -> DEP_13_BOLIVAR, Sucre -> DEP_70_SUCRE)
        dep_code = hierarchy.department_code
        applicable_scopes.add(f"DEP_{dep_code}")
        if dep_code == "13":
            applicable_scopes.add("DEP_13_BOLIVAR")
        elif dep_code == "70":
            applicable_scopes.add("DEP_70_SUCRE")
        else:
            dep_clean = hierarchy.department_name.upper().replace("Í", "I").replace("Á", "A").replace("É", "E").replace("Ó", "O").replace("Ú", "U")
            applicable_scopes.add(f"DEP_{dep_code}_{dep_clean}")

        # 2. Explorar catálogo de fuentes oficiales
        for source_id, entry in self.verifier.registered_sources.items():
            # Filtrar por alcance territorial
            if entry.territory_scope not in applicable_scopes:
                continue

            # Mapear instrumentos ofrecidos por esta fuente
            supported_instruments = SOURCE_TO_INSTRUMENTS.get(source_id, [])
            matched_instruments = [inst for inst in query.instrument_types if inst in supported_instruments]
            if not matched_instruments:
                continue

            matched_inst = matched_instruments[0]

            # 3. Filtrado de dominio oficial estricto
            normalized_url = entry.canonical_url.strip()
            if not self.is_official_domain(normalized_url):
                continue

            # Deduplicación por URL
            if normalized_url in seen_urls:
                continue
            seen_urls.add(normalized_url)

            # 4. Evaluación de estado y simulación/mock de cabeceras
            http_status: int | None = None
            content_type: str | None = None
            status: DiscoveryStatus = "candidate"
            confidence: ConfidenceLevel = "high"
            selection_reason = (
                f"Fuente oficial de {entry.entity} con cobertura para {entry.territory_scope} "
                f"aplicable al territorio {hierarchy.municipality_name}."
            )

            if self._url_probe_fn:
                probe = self._url_probe_fn(normalized_url)
                http_status = probe.get("status_code")
                content_type = probe.get("content_type")

                # Regla de integridad: si es documental (espera PDF) pero recibe HTML, requiere revisión
                if entry.pipeline_type == "documental":
                    if http_status == 200 and content_type and "application/pdf" not in content_type.lower():
                        status = "requires_review"
                        confidence = "medium"
                        selection_reason += " Alerta: Content-Type no corresponde a binario PDF."
                    elif http_status == 200:
                        status = "available"
                    elif http_status == 404:
                        status = "unavailable"
                        confidence = "low"
                        selection_reason += " Alerta: Recurso no disponible en servidor remoto (404)."
                    else:
                        status = "requires_review"
                        confidence = "medium"
                else:
                    # Pipeline tabular (datos abiertos / JSON API)
                    if http_status == 200 and content_type and "json" in content_type.lower():
                        status = "available"
                    elif http_status == 200:
                        status = "available"
                    else:
                        status = "candidate"
            else:
                # Modo offline determinista: sin llamada HTTP en esta ejecución, la fuente permanece como candidata
                status = "candidate"
                http_status = None
                content_type = None

            # 5. Separación obligatoria de pipelines
            # Documental -> document_context
            # Tabular -> tabular_context
            source_type = "document_context" if entry.pipeline_type == "documental" else "tabular_context"

            record = CandidateSourceRecord(
                source_id=source_id,
                url=normalized_url,
                entity=entry.entity,
                title=entry.name,
                territory_scope=entry.territory_scope,
                instrument_type=matched_inst,
                pipeline_type=entry.pipeline_type,
                document_format=entry.document_format,
                status=status,
                confidence_level=confidence,
                selection_reason=selection_reason,
                http_status=http_status,
                content_type=content_type,
                query_date=now_iso,
                source_type=source_type,
                allowed_for_training=False,
                usage_state="context_only",
                consent_status="not_applicable",
                approval_status="pending_review",
            )
            candidates.append(record)

            if len(candidates) >= query.max_candidates:
                break

        return DiscoveryResult(
            query=query,
            resolved_hierarchy=hierarchy,
            candidates=candidates,
            total_candidates=len(candidates),
            discovery_timestamp=now_iso,
        )
