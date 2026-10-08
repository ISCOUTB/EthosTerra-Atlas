import os
import random
import time
import urllib.robotparser
from urllib.parse import urlparse
import httpx


def build_transparent_user_agent() -> str:
    """Construye el User-Agent transparente leyendo obligatoriamente ATLAS_CONTACT_EMAIL."""
    email = os.environ.get("ATLAS_CONTACT_EMAIL", "").strip()
    if not email:
        raise ValueError(
            "Variable de entorno obligatoria ATLAS_CONTACT_EMAIL no definida. "
            "Se requiere un correo de contacto real e institucional para la identificación transparente del User-Agent. Abortando operación."
        )
    return f"AtlasTerritorial-Collector/1.0 (Investigacion Posgrado Montes de Maria; Contacto: {email})"


class CircuitBreakerOpenError(Exception):
    """Error cuando el circuit breaker de un host está activo por fallos recurrentes."""
    pass


class RobotsDisallowedError(Exception):
    """Error cuando robots.txt prohíbe el rastreo de una URL."""
    pass


class CrawlBudgetExceededError(Exception):
    """Error cuando se alcanza el presupuesto máximo de solicitudes o bytes."""
    pass


class RobotsTxtManager:
    """Administrador y caché de políticas robots.txt por host."""

    def __init__(self, user_agent: str | None = None) -> None:
        self.user_agent = user_agent if user_agent is not None else build_transparent_user_agent()
        self._cache: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    def get_parser(self, host: str, client: httpx.Client | None = None) -> urllib.robotparser.RobotFileParser | None:
        if host in self._cache:
            return self._cache[host]

        robots_url = f"https://{host}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)

        try:
            c = client or httpx.Client(timeout=5.0, verify=True)
            resp = c.get(robots_url, headers={"User-Agent": self.user_agent})
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
                self._cache[host] = rp
                return rp
            elif resp.status_code in (404, 410):
                # Si no existe robots.txt, se asume permitido todo
                self._cache[host] = None
                return None
            else:
                # Ante error 5xx o 403 en robots.txt, ser conservador pero cachear None
                self._cache[host] = None
                return None
        except Exception:
            self._cache[host] = None
            return None

    def can_fetch(self, url: str, client: httpx.Client | None = None) -> bool:
        """Determina si la URL puede ser rastreada respetando robots.txt."""
        parsed = urlparse(url)
        host = parsed.netloc
        if not host:
            return False

        rp = self.get_parser(host, client=client)
        if rp is None:
            return True
        return rp.can_fetch(self.user_agent, url)

    def get_crawl_delay(self, url: str) -> float | None:
        parsed = urlparse(url)
        host = parsed.netloc
        if host in self._cache and self._cache[host] is not None:
            rp = self._cache[host]
            delay = rp.crawl_delay(self.user_agent)
            if delay is not None:
                return float(delay)
        return None


class HostRateLimiter:
    """Garantiza concurrencia 1 por host y retraso adaptativo con jitter."""

    def __init__(self, base_delay: float = 2.0) -> None:
        self.base_delay = base_delay
        self._last_request_time: dict[str, float] = {}

    def wait_for_turn(self, host: str, crawl_delay: float | None = None) -> None:
        """Aplica espera obligatoria antes de realizar una solicitud al host."""
        now = time.time()
        last = self._last_request_time.get(host, 0.0)
        delay = crawl_delay if crawl_delay is not None else self.base_delay
        jitter = random.uniform(0.1, 0.4)
        target_delay = delay + jitter

        elapsed = now - last
        if elapsed < target_delay:
            sleep_time = target_delay - elapsed
            time.sleep(sleep_time)

        self._last_request_time[host] = time.time()


class CircuitBreaker:
    """Circuit breaker por host ante errores recurrentes (429, 503, timeouts)."""

    def __init__(self, max_failures: int = 3, cooldown_seconds: float = 60.0) -> None:
        self.max_failures = max_failures
        self.cooldown_seconds = cooldown_seconds
        self._failures: dict[str, int] = {}
        self._opened_at: dict[str, float] = {}

    def check_host(self, host: str) -> None:
        if host in self._opened_at:
            opened_time = self._opened_at[host]
            if time.time() - opened_time < self.cooldown_seconds:
                remaining = int(self.cooldown_seconds - (time.time() - opened_time))
                raise CircuitBreakerOpenError(
                    f"Circuit breaker activo para '{host}' por fallos recurrentes. Enfriamiento: {remaining}s."
                )
            else:
                # Período de enfriamiento superado: restablecer
                del self._opened_at[host]
                self._failures[host] = 0

    def record_success(self, host: str) -> None:
        self._failures[host] = 0
        self._opened_at.pop(host, None)

    def record_failure(self, host: str, retry_after: float | None = None) -> None:
        count = self._failures.get(host, 0) + 1
        self._failures[host] = count

        if retry_after is not None and retry_after > 0:
            self._opened_at[host] = time.time()
            self.cooldown_seconds = max(self.cooldown_seconds, retry_after)
        elif count >= self.max_failures:
            self._opened_at[host] = time.time()


class CrawlBudgetTracker:
    """Controla y audita el consumo de presupuesto de peticiones y bytes."""

    def __init__(
        self,
        max_requests: int = 20,
        max_depth: int = 2,
        max_candidates: int = 10,
        max_bytes: int = 100 * 1024 * 1024,
    ) -> None:
        self.max_requests = max_requests
        self.max_depth = max_depth
        self.max_candidates = max_candidates
        self.max_bytes = max_bytes

        self.requests_count = 0
        self.bytes_transferred = 0
        self.candidates_count = 0
        self.attempts_log: list[dict] = []
        self.discards_log: list[dict] = []

    def can_request(self) -> bool:
        return self.requests_count < self.max_requests

    def record_request(self, url: str, status_code: int | None, byte_size: int = 0) -> None:
        self.requests_count += 1
        self.bytes_transferred += byte_size
        self.attempts_log.append({
            "url": url,
            "status_code": status_code,
            "bytes": byte_size,
            "timestamp": time.time(),
        })

        if self.bytes_transferred > self.max_bytes:
            raise CrawlBudgetExceededError(
                f"Presupuesto de bytes excedido ({self.bytes_transferred} > {self.max_bytes})."
            )

    def record_discard(self, url: str, reason: str) -> None:
        self.discards_log.append({
            "url": url,
            "reason": reason,
            "timestamp": time.time(),
        })
