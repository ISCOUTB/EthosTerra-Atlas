from pathlib import Path
import sys
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.atlas.web.politeness import (
    RobotsTxtManager,
    HostRateLimiter,
    CircuitBreaker,
    CrawlBudgetTracker,
    CircuitBreakerOpenError,
    CrawlBudgetExceededError,
)


def test_robots_txt_parsing_and_permission():
    """Valida que RobotsTxtManager respete reglas de robots.txt."""
    mgr = RobotsTxtManager(user_agent="AtlasTerritorialBot/1.0 (test@atlas.test)")
    # Mocking parser directo
    import urllib.robotparser
    rp = urllib.robotparser.RobotFileParser()
    rp.parse([
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /privado/",
        "Allow: /descargas/",
    ])
    mgr._cache["www.renovacionterritorio.gov.co"] = rp

    assert mgr.can_fetch("https://www.renovacionterritorio.gov.co/descargas/patr.pdf")
    assert not mgr.can_fetch("https://www.renovacionterritorio.gov.co/admin/dashboard")
    assert not mgr.can_fetch("https://www.renovacionterritorio.gov.co/privado/archivo")


def test_circuit_breaker_behavior():
    """Circuit breaker se activa tras 3 fallos y bloquea solicitudes."""
    cb = CircuitBreaker(max_failures=3, cooldown_seconds=30.0)
    host = "www.adr.gov.co"

    # 1 y 2 fallos: host aún habilitado
    cb.record_failure(host)
    cb.check_host(host)
    cb.record_failure(host)
    cb.check_host(host)

    # 3 fallos: se abre el circuito
    cb.record_failure(host)
    with pytest.raises(CircuitBreakerOpenError) as exc:
        cb.check_host(host)
    assert "Circuit breaker activo" in str(exc.value)

    # Si se registra éxito en otro host, no afecta al bloqueado
    cb.record_success("www.renovacionterritorio.gov.co")
    with pytest.raises(CircuitBreakerOpenError):
        cb.check_host(host)


def test_crawl_budget_tracker_limits():
    """Valida los límites de solicitudes y cuota de bytes en el presupuesto."""
    tracker = CrawlBudgetTracker(max_requests=2, max_bytes=1000)

    assert tracker.can_request()
    tracker.record_request("https://a.gov.co/1", 200, 400)
    assert tracker.can_request()
    tracker.record_request("https://a.gov.co/2", 200, 400)
    assert not tracker.can_request()

    # Superar límite de bytes dispara excepción
    with pytest.raises(CrawlBudgetExceededError):
        tracker.record_request("https://a.gov.co/3", 200, 300)


def test_host_rate_limiter_timestamps():
    """Valida que HostRateLimiter registre turnos sin excepciones."""
    limiter = HostRateLimiter(base_delay=0.01)
    limiter.wait_for_turn("www.dnp.gov.co")
    assert "www.dnp.gov.co" in limiter._last_request_time


def test_transparent_user_agent_requires_env_var(monkeypatch):
    """Valida que el User-Agent aborte si ATLAS_CONTACT_EMAIL no está definida."""
    from apps.atlas.web.politeness import build_transparent_user_agent

    monkeypatch.delenv("ATLAS_CONTACT_EMAIL", raising=False)
    with pytest.raises(ValueError) as exc:
        build_transparent_user_agent()
    assert "ATLAS_CONTACT_EMAIL no definida" in str(exc.value)

    monkeypatch.setenv("ATLAS_CONTACT_EMAIL", "contacto@universidad.edu.co")
    ua = build_transparent_user_agent()
    assert "contacto@universidad.edu.co" in ua
    assert "AtlasTerritorial-Collector/1.0" in ua
