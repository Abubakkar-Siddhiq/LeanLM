from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from db.session import get_session
from api.auth.dependencies import get_current_user
from db.models import User
from api.providers.schemas import (
    ProviderKeyCreate,
    ProviderKeyResponse,
    ProviderKeyValidateResponse,
    ProviderAvailabilityResponse,
)
from api.providers.services import ProviderKeyService


router = APIRouter()
provider_key_service = ProviderKeyService()


@router.post(
    "/providers",
    response_model=ProviderKeyResponse,
    status_code=201,
    tags=["providers"],
)
def create_provider_key(
    payload: ProviderKeyCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        return provider_key_service.create_provider_key(session, payload, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/providers",
    response_model=list[ProviderKeyResponse],
    tags=["providers"],
)
def list_provider_keys(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return provider_key_service.list_provider_keys(session, current_user.id)


@router.delete(
    "/providers/{provider_name}",
    response_model=ProviderKeyResponse,
    tags=["providers"],
)
def delete_provider_key(
    provider_name: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = provider_key_service.delete_provider_key(session, provider_name, current_user.id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No provider key found for '{provider_name}'",
        )
    return result


@router.post(
    "/providers/{provider_name}/validate",
    response_model=ProviderKeyValidateResponse,
    tags=["providers"],
)
def validate_provider_key(
    provider_name: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return provider_key_service.validate_provider_key(session, provider_name, current_user.id)


@router.get(
    "/providers/available",
    response_model=ProviderAvailabilityResponse,
    tags=["providers"],
)
def get_available_providers(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    available = provider_key_service.get_available_providers(session, current_user.id)
    return ProviderAvailabilityResponse(available_providers=available)
