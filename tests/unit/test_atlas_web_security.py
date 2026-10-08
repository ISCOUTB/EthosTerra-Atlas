from pathlib import Path
import sys
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.atlas.web.security import (
    validate_url_security,
    validate_pdf_magic_bytes,
    is_authorized_authority_host,
    SecurityValidationError,
)


def test_https_enforcement():
    """Solo permite HTTPS; rechaza esquemas http, ftp, file, etc."""
    with pytest.raises(SecurityValidationError) as exc:
        validate_url_security("http://www.renovacionterritorio.gov.co/doc.pdf", resolve_dns=False)
    assert "Solo se permite HTTPS" in str(exc.value)

    with pytest.raises(SecurityValidationError):
        validate_url_security("file:///etc/passwd", resolve_dns=False)

    with pytest.raises(SecurityValidationError):
        validate_url_security("ftp://www.adr.gov.co/doc.pdf", resolve_dns=False)


def test_authorized_authority_allowlist():
    """Valida la allowlist explícita por autoridad institucional."""
    # Autoridades válidas
    assert is_authorized_authority_host("renovacionterritorio.gov.co")
    assert is_authorized_authority_host("www.renovacionterritorio.gov.co")
    assert is_authorized_authority_host("adr.gov.co")
    assert is_authorized_authority_host("www.adr.gov.co")
    assert is_authorized_authority_host("datos.gov.co")
    assert is_authorized_authority_host("bolivar.gov.co")
    assert is_authorized_authority_host("elcarmendebolivar-bolivar.gov.co")

    # Dominios no autorizados / de terceros / genéricos
    assert not is_authorized_authority_host("wikipedia.org")
    assert not is_authorized_authority_host("google.com")
    assert not is_authorized_authority_host("fake-renovacionterritorio.com")
    assert not is_authorized_authority_host("compromised.gov.co.attacker.com")

    # Exclusión estricta de subdominios de la ART
    assert not is_authorized_authority_host("portalart.renovacionterritorio.gov.co")
    assert not is_authorized_authority_host("erp.renovacionterritorio.gov.co")
    assert not is_authorized_authority_host("gisart.renovacionterritorio.gov.co")


def test_reject_untrusted_domain_url():
    """Rechaza URLs que no pertenecen a autoridades autorizadas."""
    with pytest.raises(SecurityValidationError) as exc:
        validate_url_security("https://external-storage.aws.com/doc.pdf", resolve_dns=False)
    assert "no pertenece a la lista de autoridades" in str(exc.value)


def test_ssrf_blocks_private_and_loopback_ips(monkeypatch):
    """Protección SSRF bloquea IPs privadas, loopback y reservadas."""
    # Simular resolución DNS a IP loopback
    def mock_getaddrinfo_loopback(host, port, proto=0):
        return [(2, 1, 6, "", ("127.0.0.1", 443))]

    monkeypatch.setattr("socket.getaddrinfo", mock_getaddrinfo_loopback)
    with pytest.raises(SecurityValidationError) as exc:
        validate_url_security("https://www.adr.gov.co/doc.pdf", resolve_dns=True)
    assert "SSRF bloqueado" in str(exc.value)
    assert "127.0.0.1" in str(exc.value)

    # Simular resolución DNS a IP privada 192.168.1.50
    def mock_getaddrinfo_private(host, port, proto=0):
        return [(2, 1, 6, "", ("192.168.1.50", 443))]

    monkeypatch.setattr("socket.getaddrinfo", mock_getaddrinfo_private)
    with pytest.raises(SecurityValidationError) as exc:
        validate_url_security("https://www.adr.gov.co/doc.pdf", resolve_dns=True)
    assert "SSRF bloqueado" in str(exc.value)
    assert "192.168.1.50" in str(exc.value)


def test_validate_pdf_magic_bytes():
    """Valida la firma mágica obligatoria (%PDF-)."""
    assert validate_pdf_magic_bytes(b"%PDF-1.4\nrest of file...")
    assert validate_pdf_magic_bytes(b"%PDF-2.0 valid")
    assert not validate_pdf_magic_bytes(b"<!DOCTYPE html><html>")
    assert not validate_pdf_magic_bytes(b"\x89PNG\r\n\x1a\n")
    assert not validate_pdf_magic_bytes(b"")
    assert not validate_pdf_magic_bytes(b"PK\x03\x04")
