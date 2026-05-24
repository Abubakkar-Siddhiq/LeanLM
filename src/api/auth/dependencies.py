from uuid import UUID
from datetime import datetime, timezone

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import PyJWKClient, PyJWKClientError, decode as jwt_decode, InvalidTokenError
from sqlmodel import Session, select

from config.settings import settings
from db.session import get_session
from db.models import User


bearer_scheme = HTTPBearer(auto_error=False)
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        if not settings.SUPABASE_URL:
            raise RuntimeError("SUPABASE_URL is not configured")
        jwks_url = settings.SUPABASE_JWKS_URL
        if not jwks_url:
            issuer = settings.SUPABASE_JWT_ISSUER or f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1"
            jwks_url = f"{issuer}/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
    return _jwks_client


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = credentials.credentials

    try:
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)
        payload = jwt_decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience="authenticated",
            issuer=settings.SUPABASE_JWT_ISSUER or f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1",
            options={"require": ["exp", "sub"]},
        )
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except PyJWKClientError:
        raise HTTPException(status_code=503, detail="Authentication service temporarily unavailable")
    except RuntimeError as e:
        if "SUPABASE_URL" in str(e):
            raise HTTPException(status_code=500, detail="Authentication not configured")
        raise

    supabase_user_id: str = payload.get("sub")
    email: str | None = payload.get("email")

    user = session.exec(
        select(User).where(User.supabase_user_id == supabase_user_id)
    ).first()

    if user is None:
        user = User(supabase_user_id=supabase_user_id, email=email)
        session.add(user)
        session.commit()
        session.refresh(user)
    elif email and user.email != email:
        user.email = email
        user.updated_at = datetime.now(timezone.utc)
        session.add(user)
        session.commit()
        session.refresh(user)

    return user
