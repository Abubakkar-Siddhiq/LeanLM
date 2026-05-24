from uuid import UUID

from sqlmodel import Session, select

from db.provider_keys import ProviderKey
from api.providers.schemas import (
    ProviderKeyCreate,
    ProviderKeyResponse,
    ProviderKeyValidateResponse,
    SUPPORTED_PROVIDERS,
)
from core.security import encrypt_api_key, decrypt_api_key


class ProviderKeyService:
    def _to_response(self, key: ProviderKey) -> ProviderKeyResponse:
        return ProviderKeyResponse(
            id=key.id,
            provider_name=key.provider_name,
            is_active=key.is_active,
            created_at=key.created_at,
            updated_at=key.updated_at,
        )

    def create_provider_key(
        self, session: Session, payload: ProviderKeyCreate, user_id: UUID
    ) -> ProviderKeyResponse:
        provider_name = payload.provider_name

        if not payload.api_key:
            raise ValueError("API key cannot be empty")

        encrypted = encrypt_api_key(payload.api_key)

        existing = session.exec(
            select(ProviderKey).where(
                ProviderKey.user_id == user_id,
                ProviderKey.provider_name == provider_name,
            )
        ).first()

        if existing:
            existing.encrypted_api_key = encrypted
            existing.is_active = True
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return self._to_response(existing)

        key = ProviderKey(
            user_id=user_id,
            provider_name=provider_name,
            encrypted_api_key=encrypted,
            is_active=True,
        )
        session.add(key)
        session.commit()
        session.refresh(key)
        return self._to_response(key)

    def list_provider_keys(self, session: Session, user_id: UUID) -> list[ProviderKeyResponse]:
        keys = session.exec(
            select(ProviderKey).where(ProviderKey.user_id == user_id)
        ).all()
        return [self._to_response(k) for k in keys]

    def delete_provider_key(
        self, session: Session, provider_name: str, user_id: UUID
    ) -> ProviderKeyResponse | None:
        provider_name = provider_name.strip().lower()
        key = session.exec(
            select(ProviderKey).where(
                ProviderKey.user_id == user_id,
                ProviderKey.provider_name == provider_name,
            )
        ).first()
        if key is None:
            return None
        key.is_active = False
        session.add(key)
        session.commit()
        session.refresh(key)
        return self._to_response(key)

    def validate_provider_key(
        self, session: Session, provider_name: str, user_id: UUID
    ) -> ProviderKeyValidateResponse:
        provider_name = provider_name.strip().lower()

        if provider_name not in SUPPORTED_PROVIDERS:
            return ProviderKeyValidateResponse(
                provider_name=provider_name,
                valid=False,
                message=f"Unsupported provider '{provider_name}'",
            )

        key = session.exec(
            select(ProviderKey).where(
                ProviderKey.user_id == user_id,
                ProviderKey.provider_name == provider_name,
                ProviderKey.is_active == True,
            )
        ).first()

        if key is None:
            return ProviderKeyValidateResponse(
                provider_name=provider_name,
                valid=False,
                message="No active provider key found",
            )

        return ProviderKeyValidateResponse(
            provider_name=provider_name,
            valid=True,
            message="Provider key is stored and active",
        )

    def get_available_providers(self, session: Session, user_id: UUID) -> list[str]:
        keys = session.exec(
            select(ProviderKey).where(
                ProviderKey.user_id == user_id,
                ProviderKey.is_active == True,
            )
        ).all()
        return [k.provider_name for k in keys]

    def get_decrypted_api_key(
        self, session: Session, provider_name: str, user_id: UUID
    ) -> str | None:
        key = session.exec(
            select(ProviderKey).where(
                ProviderKey.user_id == user_id,
                ProviderKey.provider_name == provider_name,
                ProviderKey.is_active == True,
            )
        ).first()
        if key is None:
            return None
        return decrypt_api_key(key.encrypted_api_key)
