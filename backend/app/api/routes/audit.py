from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...audit.service import AuditLogger
from ...core.config import Settings, get_settings
from ...core.schemas import ActorContext, AuditEvent
from ...core.security import require_scopes

router = APIRouter(prefix="/audit", tags=["audit"])


def get_audit_logger(settings: Annotated[Settings, Depends(get_settings)]) -> AuditLogger:
    return AuditLogger(settings)


@router.get("/events", response_model=list[AuditEvent])
def list_audit_events(
    actor: Annotated[ActorContext, Depends(require_scopes("audit:read"))],
    logger: Annotated[AuditLogger, Depends(get_audit_logger)],
    limit: int = Query(default=20, ge=1, le=100),
) -> list[AuditEvent]:
    _ = actor
    return logger.list_events(limit=limit)


@router.get("/events/{event_id}", response_model=AuditEvent)
def get_audit_event(
    event_id: str,
    actor: Annotated[ActorContext, Depends(require_scopes("audit:read"))],
    logger: Annotated[AuditLogger, Depends(get_audit_logger)],
) -> AuditEvent:
    _ = actor
    event = logger.get_event(event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit event not found.",
        )
    return event
