from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

# Allowlist explícita por autoridad institucional colombiana
AUTHORIZED_AUTHORITY_DOMAINS: frozenset[str] = frozenset({
    # Entidades del orden nacional
    "renovacionterritorio.gov.co",
    "www.renovacionterritorio.gov.co",
    "adr.gov.co",
    "www.adr.gov.co",
    "dnp.gov.co",
    "www.dnp.gov.co",
    "terridata.dnp.gov.co",
    "colaboracion.dnp.gov.co",
    "dane.gov.co",
    "www.dane.gov.co",
    "upra.gov.co",
    "www.upra.gov.co",
    "datos.gov.co",
    "www.datos.gov.co",
    "minagricultura.gov.co",
    "www.minagricultura.gov.co",
    # Gobernaciones y Asambleas de territorios piloto
    "bolivar.gov.co",
    "www.bolivar.gov.co",
    "sucre.gov.co",
    "www.sucre.gov.co",
    # Alcaldías de municipios piloto
    "elcarmendebolivar-bolivar.gov.co",
    "www.elcarmendebolivar-bolivar.gov.co",
    "sanjacinto-bolivar.gov.co",
    "www.sanjacinto-bolivar.gov.co",
    "sanjuannepomuceno-bolivar.gov.co",
    "www.sanjuannepomuceno-bolivar.gov.co",
    "marialabaja-bolivar.gov.co",
    "www.marialabaja-bolivar.gov.co",
    "sanonofre-sucre.gov.co",
    "www.sanonofre-sucre.gov.co",
})

PDF_MAGIC_BYTES = b"%PDF-"


class SecurityValidationError(Exception):
    """Error emitido cuando una URL o artefacto viola las políticas de seguridad."""
    pass


EXCLUDED_HOSTS: frozenset[str] = frozenset({
    "portalart.renovacionterritorio.gov.co",
    "erp.renovacionterritorio.gov.co",
    "gisart.renovacionterritorio.gov.co",
})


def is_authorized_authority_host(hostname: str) -> bool:
    """Valida que el hostname pertenezca a la allowlist explícita por autoridad."""
    if not hostname:
        return False
    host_clean = hostname.strip().lower()

    # Exclusión explícita de subdominios prohibidos de la ART
    if host_clean in EXCLUDED_HOSTS or any(ex in host_clean for ex in ("portalart.", "erp.", "gisart.")):
        return False

    # Regla estricta para la ART: solo se permite el host principal www.renovacionterritorio.gov.co
    if host_clean.endswith("renovacionterritorio.gov.co"):
        return host_clean in ("www.renovacionterritorio.gov.co", "renovacionterritorio.gov.co")

    if host_clean in AUTHORIZED_AUTHORITY_DOMAINS:
        return True

    # Comprobar subdominios de autoridades autorizadas
    for auth_domain in AUTHORIZED_AUTHORITY_DOMAINS:
        if host_clean.endswith("." + auth_domain):
            return True

    return False


def validate_url_security(url: str, resolve_dns: bool = True) -> str:
    """Valida que la URL sea segura: HTTPS estricto, dominio en allowlist y protección SSRF."""
    if not url or not isinstance(url, str):
        raise SecurityValidationError("URL vacía o no válida.")

    parsed = urlparse(url.strip())

    # 1. Forzar HTTPS estricto
    if parsed.scheme.lower() != "https":
        raise SecurityValidationError(f"Protocolo inseguro '{parsed.scheme}'. Solo se permite HTTPS.")

    hostname = parsed.hostname
    if not hostname:
        raise SecurityValidationError("La URL no contiene un nombre de host válido.")

    # 2. Validar Allowlist de autoridades oficiales
    if not is_authorized_authority_host(hostname):
        raise SecurityValidationError(
            f"El host '{hostname}' no pertenece a la lista de autoridades oficiales autorizadas."
        )

    # 3. Protección SSRF: Resolución DNS y bloqueo de IPs no públicas
    if resolve_dns:
        try:
            addr_info = socket.getaddrinfo(hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
            for item in addr_info:
                ip_str = item[4][0]
                ip_obj = ipaddress.ip_address(ip_str)
                if (
                    ip_obj.is_private
                    or ip_obj.is_loopback
                    or ip_obj.is_link_local
                    or ip_obj.is_reserved
                    or ip_obj.is_multicast
                    or ip_obj.is_unspecified
                ):
                    raise SecurityValidationError(
                        f"SSRF bloqueado: El host '{hostname}' resolvió a la dirección no pública '{ip_str}'."
                    )
        except socket.gaierror as exc:
            raise SecurityValidationError(f"Fallo al resolver DNS para '{hostname}': {exc}") from exc

    return url.strip()


def validate_pdf_magic_bytes(header_bytes: bytes) -> bool:
    """Verifica que los primeros bytes del archivo correspondan al encabezado mágico de PDF (%PDF-)."""
    if not header_bytes or len(header_bytes) < len(PDF_MAGIC_BYTES):
        return False
    return header_bytes.startswith(PDF_MAGIC_BYTES)
