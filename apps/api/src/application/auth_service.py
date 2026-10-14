"""Servicio soberano de autenticación, hashing criptográfico y gestión de tokens JWT."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    from src.domain.auth_schemas import (
        LoginRequest,
        TokenResponse,
        UserProfile,
        UserRecord,
        ChangePasswordRequest,
    )
except ImportError:
    from apps.api.src.domain.auth_schemas import (
        LoginRequest,
        TokenResponse,
        UserProfile,
        UserRecord,
        ChangePasswordRequest,
    )

logger = logging.getLogger("auth_service")

# Clave secreta para firma criptográfica HMAC-SHA256 (inmutable salvo inyección de entorno)
SECRET_KEY = os.environ.get("AUTH_SECRET_KEY", "ethosterra-sovereign-secret-token-key-2026-montes-de-maria")
TOKEN_EXPIRY_SECONDS = int(os.environ.get("AUTH_TOKEN_EXPIRY_SECONDS", "28800"))  # 8 horas por defecto


def _base64url_encode(data: bytes) -> str:
    """Codificación Base64URL conforme a RFC 7519 sin padding '='."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _base64url_decode(data: str) -> bytes:
    """Decodificación Base64URL agregando el padding necesario."""
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + padding)


class AuthService:
    """Gestor criptográfico y de almacenamiento persistente de credenciales de usuario."""

    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self.storage_dir = storage_dir or Path("outputs/auth")
        self.users_file = self.storage_dir / "users.json"
        self._lock = threading.Lock()
        self._ensure_storage_and_seed_admin()

    def _ensure_storage_and_seed_admin(self) -> None:
        """Crea el directorio y si no existe el almacén, genera el usuario admin inicial determinista."""
        with self._lock:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            if not self.users_file.exists() or self.users_file.stat().st_size == 0:
                logger.info("Inicializando almacén de usuarios soberano en outputs/auth/users.json")
                initial_admin_pwd = os.environ.get("INITIAL_ADMIN_PASSWORD", "EthosTerra2026!")
                salt, pwd_hash = self.hash_password(initial_admin_pwd)
                now_iso = datetime.now(timezone.utc).isoformat()

                admin_record = UserRecord(
                    username="admin",
                    password_hash=pwd_hash,
                    salt=salt,
                    role="admin",
                    display_name="Administrador Soberano",
                    is_active=True,
                    created_at=now_iso,
                    updated_at=now_iso,
                )
                users_map = {"admin": admin_record.model_dump()}
                self.users_file.write_text(json.dumps(users_map, indent=2, ensure_ascii=False), encoding="utf-8")
                logger.info("Usuario inicial 'admin' creado exitosamente.")

    def _load_users(self) -> Dict[str, UserRecord]:
        """Carga el registro de usuarios desde disco con validación de modelo."""
        if not self.users_file.exists():
            return {}
        try:
            data = json.loads(self.users_file.read_text(encoding="utf-8"))
            return {k: UserRecord.model_validate(v) for k, v in data.items()}
        except Exception as exc:
            logger.error(f"Error leyendo almacén de usuarios: {exc}")
            return {}

    def _save_users(self, users: Dict[str, UserRecord]) -> None:
        """Guarda de forma atómica el registro de usuarios en disco."""
        data = {k: v.model_dump() for k, v in users.items()}
        tmp_file = self.users_file.with_suffix(".tmp")
        tmp_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp_file.replace(self.users_file)

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Genera hash criptográfico seguro PBKDF2-HMAC-SHA256 con 100,000 iteraciones."""
        if not salt:
            salt = os.urandom(16).hex()
        pwd_hash = hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=password.encode("utf-8"),
            salt=salt.encode("utf-8"),
            iterations=100_000,
        ).hex()
        return salt, pwd_hash

    @classmethod
    def verify_password(cls, password: str, salt: str, expected_hash: str) -> bool:
        """Verifica una contraseña candidata usando comparación en tiempo constante (anti-timing attack)."""
        _, computed_hash = cls.hash_password(password, salt)
        return hmac.compare_digest(computed_hash, expected_hash)

    def authenticate_user(self, login_req: LoginRequest) -> Optional[UserProfile]:
        """Valida credenciales contra el almacén local. Retorna el perfil o None si falla."""
        with self._lock:
            users = self._load_users()
            user = users.get(login_req.username)
            if not user or not user.is_active:
                logger.warning(f"Intento de autenticación fallido: usuario '{login_req.username}' no existe o está inactivo.")
                return None

            if not self.verify_password(login_req.password, user.salt, user.password_hash):
                logger.warning(f"Intento de autenticación fallido: contraseña inválida para '{login_req.username}'.")
                return None

            logger.info(f"Usuario '{user.username}' autenticado exitosamente.")
            return UserProfile(
                username=user.username,
                role=user.role,
                display_name=user.display_name,
                is_active=user.is_active,
            )

    def create_access_token(self, profile: UserProfile, expires_delta: Optional[int] = None) -> str:
        """Genera un JWT firmado con HMAC-SHA256 conforme a RFC 7519."""
        now = int(time.time())
        exp = now + (expires_delta or TOKEN_EXPIRY_SECONDS)

        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": profile.username,
            "role": profile.role,
            "display_name": profile.display_name,
            "iat": now,
            "exp": exp,
            "iss": "ethosterra-atlas-auth",
        }

        header_b64 = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_b64 = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

        signature = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
        sig_b64 = _base64url_encode(signature)

        return f"{header_b64}.{payload_b64}.{sig_b64}"

    def verify_token(self, token: str) -> Optional[UserProfile]:
        """Valida criptográficamente la firma del JWT y la vigencia del tiempo de expiración."""
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

        # 1. Verificación de la firma HMAC-SHA256 en tiempo constante
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
        try:
            provided_sig = _base64url_decode(sig_b64)
            if not hmac.compare_digest(expected_sig, provided_sig):
                return None
        except Exception:
            return None

        # 2. Parseo del payload y verificación de expiración
        try:
            payload_bytes = _base64url_decode(payload_b64)
            payload = json.loads(payload_bytes.decode("utf-8"))
        except Exception:
            return None

        exp = payload.get("exp")
        if not exp or int(exp) < int(time.time()):
            logger.debug("Token JWT expirado.")
            return None

        username = payload.get("sub")
        if not username:
            return None

        # 3. Confirmación de que el usuario sigue existiendo y está activo
        with self._lock:
            users = self._load_users()
            user = users.get(username)
            if not user or not user.is_active:
                return None

            return UserProfile(
                username=user.username,
                role=user.role,
                display_name=user.display_name,
                is_active=user.is_active,
            )

    def change_password(self, username: str, req: ChangePasswordRequest) -> bool:
        """Cambia la contraseña de un usuario verificando previamente su clave actual."""
        with self._lock:
            users = self._load_users()
            user = users.get(username)
            if not user:
                return False

            if not self.verify_password(req.current_password, user.salt, user.password_hash):
                return False

            new_salt, new_hash = self.hash_password(req.new_password)
            user.salt = new_salt
            user.password_hash = new_hash
            user.updated_at = datetime.now(timezone.utc).isoformat()
            users[username] = user
            self._save_users(users)
            logger.info(f"Contraseña actualizada para el usuario '{username}'.")
            return True
