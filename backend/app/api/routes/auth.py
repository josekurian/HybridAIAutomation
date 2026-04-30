from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ...core.config import Settings, get_settings
from ...core.schemas import ActorContext, TokenRequest, TokenResponse
from ...core.security import ROLE_SCOPES, create_access_token, get_actor_context

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
def issue_token(
    payload: TokenRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    if (
        payload.username != settings.demo_admin_user
        or payload.password != settings.demo_admin_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid demo credentials.",
        )

    token = create_access_token(subject=payload.username, settings=settings, role="demo-admin")
    return TokenResponse(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
        role="demo-admin",
        scopes=ROLE_SCOPES["demo-admin"],
    )


@router.get("/me", response_model=ActorContext)
def get_me(
    actor: Annotated[ActorContext, Depends(get_actor_context)],
) -> ActorContext:
    return actor
