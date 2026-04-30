from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import Settings, get_settings
from .schemas import ActorContext

bearer_scheme = HTTPBearer(auto_error=False)

ROLE_SCOPES: dict[str, list[str]] = {
    "demo-admin": [
        "agents:read",
        "agents:run",
        "workflows:read",
        "workflows:run",
        "studio:read",
        "studio:build",
        "studio:validate",
        "studio:credentials:read",
        "studio:credentials:manage",
        "studio:monitoring:read",
        "studio:integrations:read",
        "studio:integrations:run",
        "studio:marketplace:read",
        "studio:marketplace:install",
        "audit:read",
        "protocols:mcp:read",
        "protocols:mcp:execute",
        "protocols:a2a:read",
    ],
    "operator": [
        "agents:read",
        "agents:run",
        "workflows:read",
        "workflows:run",
        "studio:read",
        "studio:build",
        "studio:validate",
        "studio:monitoring:read",
        "studio:integrations:read",
        "studio:integrations:run",
        "studio:marketplace:read",
        "protocols:mcp:read",
        "protocols:mcp:execute",
        "protocols:a2a:read",
    ],
    "auditor": [
        "workflows:read",
        "studio:read",
        "studio:monitoring:read",
        "audit:read",
        "protocols:mcp:read",
        "protocols:a2a:read",
    ],
}


def create_access_token(subject: str, settings: Settings, role: str = "operator") -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    scopes = ROLE_SCOPES.get(role, ROLE_SCOPES["operator"])
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "scopes": scopes,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> ActorContext:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from exc

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject is missing.",
        )

    role = payload.get("role", "operator")
    scopes = payload.get("scopes")
    normalized_scopes = [str(scope) for scope in scopes] if isinstance(scopes, list) else ROLE_SCOPES.get(str(role), [])
    return ActorContext(subject=subject, role=str(role), auth_mode="token", scopes=normalized_scopes)


def get_actor_context(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ActorContext:
    if credentials is None:
        if settings.auth_required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bearer token is required.",
            )
        return ActorContext(subject="anonymous", auth_mode="anonymous")

    return decode_access_token(credentials.credentials, settings)


def require_scopes(*required_scopes: str):
    def dependency(
        actor: Annotated[ActorContext, Depends(get_actor_context)],
    ) -> ActorContext:
        missing = [scope for scope in required_scopes if scope not in actor.scopes]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scopes: {', '.join(missing)}.",
            )
        return actor

    return dependency
