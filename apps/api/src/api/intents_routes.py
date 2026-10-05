from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, status, Path as FPath, Response

from src.domain.v2.intent_schemas import (
    CreateIntentRequest,
    UpdateIntentRequest,
    IntentResponse,
    TrashIntentResponse,
    RestoreIntentRequest,
    PurgeTrashRequest,
    PurgeResponse,
)
from src.application.manual_intent_service import (
    ManualIntentService,
    IntentSecurityError,
    IntentNotFoundError,
    IntentAlreadyExistsError,
    IntentRetentionExpiredError,
)

# Router para CRUD manual de intenciones (B5)
intents_router = APIRouter(prefix="/intents", tags=["B5 Manual Intentions CRUD"])

# Instancia singleton del servicio
_intent_service: ManualIntentService | None = None


def get_intent_service() -> ManualIntentService:
    global _intent_service
    if _intent_service is None:
        _intent_service = ManualIntentService()
    return _intent_service


def set_intent_service(service: ManualIntentService) -> None:
    """Permite inyectar un servicio personalizado (útil para pruebas unitarias)."""
    global _intent_service
    _intent_service = service


@intents_router.post(
    "",
    response_model=IntentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una intención manual declarativa (Caso Puro o Conflictivo)",
)
def create_intent_endpoint(
    req: CreateIntentRequest,
    service: ManualIntentService = Depends(get_intent_service),
) -> IntentResponse:
    try:
        return service.create_intent(req)
    except IntentAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except IntentSecurityError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@intents_router.get(
    "",
    response_model=list[IntentResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar todas las intenciones activas",
)
def list_intents_endpoint(
    service: ManualIntentService = Depends(get_intent_service),
) -> list[IntentResponse]:
    return service.list_intents()


@intents_router.get(
    "/trash",
    response_model=list[TrashIntentResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar intenciones en papelera de reciclaje con ventana de 30 días",
)
def list_trash_endpoint(
    service: ManualIntentService = Depends(get_intent_service),
) -> list[TrashIntentResponse]:
    return service.list_trash()


@intents_router.get(
    "/{intent_id}",
    response_model=IntentResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener una intención activa por su identificador",
)
def get_intent_endpoint(
    intent_id: Annotated[str, FPath(description="Identificador único del intento")],
    service: ManualIntentService = Depends(get_intent_service),
) -> IntentResponse:
    try:
        return service.get_intent(intent_id)
    except IntentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IntentSecurityError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@intents_router.put(
    "/{intent_id}",
    response_model=IntentResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar una intención activa con validación previa de esquema",
)
def update_intent_endpoint(
    intent_id: Annotated[str, FPath(description="Identificador único del intento")],
    req: UpdateIntentRequest,
    service: ManualIntentService = Depends(get_intent_service),
) -> IntentResponse:
    try:
        return service.update_intent(intent_id, req)
    except IntentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IntentSecurityError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@intents_router.delete(
    "/{intent_id}",
    response_model=TrashIntentResponse,
    status_code=status.HTTP_200_OK,
    summary="Borrado lógico: mueve la intención a la papelera con retención de 30 días",
)
def delete_intent_endpoint(
    intent_id: Annotated[str, FPath(description="Identificador único del intento")],
    deleted_by: str = "operador_manual",
    service: ManualIntentService = Depends(get_intent_service),
) -> TrashIntentResponse:
    try:
        return service.delete_intent(intent_id, deleted_by=deleted_by)
    except IntentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IntentSecurityError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@intents_router.post(
    "/{intent_id}/restore",
    response_model=IntentResponse,
    status_code=status.HTTP_200_OK,
    summary="Restaurar una intención desde la papelera si está dentro de la ventana de retención",
)
def restore_intent_endpoint(
    intent_id: Annotated[str, FPath(description="Identificador único del intento")],
    req: RestoreIntentRequest = RestoreIntentRequest(),
    service: ManualIntentService = Depends(get_intent_service),
) -> IntentResponse:
    try:
        return service.restore_intent(intent_id, restored_by=req.restored_by)
    except IntentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IntentRetentionExpiredError as e:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(e))
    except IntentAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except IntentSecurityError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@intents_router.post(
    "/trash/purge",
    response_model=PurgeResponse,
    status_code=status.HTTP_200_OK,
    summary="Purga definitiva bajo demanda de intenciones expiradas de la papelera",
)
def purge_trash_endpoint(
    req: PurgeTrashRequest = PurgeTrashRequest(),
    service: ManualIntentService = Depends(get_intent_service),
) -> PurgeResponse:
    try:
        return service.purge_trash(purged_by=req.purged_by)
    except IntentSecurityError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
