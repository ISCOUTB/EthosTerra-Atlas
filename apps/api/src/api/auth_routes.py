"""Rutas y dependencias de seguridad para autenticación de usuarios."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

try:
    from src.domain.auth_schemas import (
        LoginRequest,
        TokenResponse,
        UserProfile,
        ChangePasswordRequest,
    )
    from src.application.auth_service import AuthService, TOKEN_EXPIRY_SECONDS
except ImportError:
    from apps.api.src.domain.auth_schemas import (
        LoginRequest,
        TokenResponse,
        UserProfile,
        ChangePasswordRequest,
    )
    from apps.api.src.application.auth_service import AuthService, TOKEN_EXPIRY_SECONDS

logger = logging.getLogger("auth_routes")

auth_router = APIRouter(prefix="/v2/auth", tags=["Autenticación y Seguridad"])
security_bearer = HTTPBearer(auto_error=False)
auth_service = AuthService()


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> UserProfile:
    """Dependencia de seguridad que valida el token Bearer criptográfico en cada petición."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida. Token Bearer ausente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    profile = auth_service.verify_token(credentials.credentials)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Bearer inválido, manipulado o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return profile


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> Optional[UserProfile]:
    """Dependencia opcional para auditoría de acciones cuando el usuario está logueado."""
    if not credentials or not credentials.credentials:
        return None
    return auth_service.verify_token(credentials.credentials)


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión soberana y obtener token Bearer JWT",
)
def login(request: LoginRequest):
    """Autentica las credenciales del usuario y emite un JWT firmado criptográficamente."""
    profile = auth_service.authenticate_user(request)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de acceso inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_service.create_access_token(profile)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=TOKEN_EXPIRY_SECONDS,
        user=profile,
    )


@auth_router.get(
    "/me",
    response_model=UserProfile,
    summary="Consultar el perfil y rol del usuario autenticado",
)
def get_me(user: UserProfile = Depends(get_current_user)):
    """Retorna los datos del perfil activo a partir de la firma del token Bearer."""
    return user


@auth_router.post(
    "/change-password",
    summary="Cambiar la contraseña del usuario autenticado",
)
def change_password(
    body: ChangePasswordRequest,
    user: UserProfile = Depends(get_current_user),
):
    """Permite al usuario autenticado actualizar su contraseña de forma segura."""
    success = auth_service.change_password(user.username, body)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta.",
        )
    return {"message": "Contraseña actualizada exitosamente."}
