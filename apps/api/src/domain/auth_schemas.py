"""Esquemas Pydantic V2 para autenticación, autorización y perfiles de usuario."""
from __future__ import annotations

import re
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class LoginRequest(BaseModel):
    """Solicitud de inicio de sesión con validación estricta anti-inyección."""
    model_config = ConfigDict(extra="forbid")

    username: str = Field(
        ...,
        min_length=3,
        max_length=32,
        description="Nombre de usuario alfanumérico (letras, números, guion y guion bajo)",
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="Contraseña del usuario",
    )

    @field_validator("username")
    @classmethod
    def validate_username_format(cls, v: str) -> str:
        trimmed = v.strip()
        # Rechaza cualquier carácter fuera del conjunto seguro para prevenir SQLi, XSS o inyección de rutas
        if not re.match(r"^[a-zA-Z0-9_\-\.]{3,32}$", trimmed):
            raise ValueError(
                "El nombre de usuario solo puede contener letras, números, puntos, guiones y guiones bajos (3 a 32 caracteres)."
            )
        return trimmed


class UserProfile(BaseModel):
    """Perfil público del usuario autenticado."""
    model_config = ConfigDict(extra="forbid")

    username: str = Field(..., description="Nombre de usuario único")
    role: Literal["admin", "territorial_curator", "agronomic_researcher", "auditor"] = Field(
        default="territorial_curator",
        description="Rol y nivel de privilegios en el sistema",
    )
    display_name: str = Field(..., description="Nombre legible para visualización")
    is_active: bool = Field(default=True, description="Estado de activación de la cuenta")


class TokenResponse(BaseModel):
    """Respuesta con token Bearer criptográfico y metadatos de sesión."""
    model_config = ConfigDict(extra="forbid")

    access_token: str = Field(..., description="Token de acceso Bearer firmado criptográficamente")
    token_type: Literal["bearer"] = Field(default="bearer", description="Tipo de token estándar")
    expires_in_seconds: int = Field(default=28800, description="Vigencia del token en segundos (8 horas)")
    user: UserProfile = Field(..., description="Perfil del usuario autenticado")


class UserRecord(BaseModel):
    """Registro persistente interno de usuario con hash seguro y salt."""
    model_config = ConfigDict(extra="forbid")

    username: str
    password_hash: str
    salt: str
    role: Literal["admin", "territorial_curator", "agronomic_researcher", "auditor"]
    display_name: str
    is_active: bool = True
    created_at: str
    updated_at: str


class ChangePasswordRequest(BaseModel):
    """Solicitud de cambio de contraseña por parte de un usuario autenticado."""
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(..., min_length=6, max_length=128)
    new_password: str = Field(..., min_length=6, max_length=128)
