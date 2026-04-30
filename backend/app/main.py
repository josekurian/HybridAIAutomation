from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes.agents import router as agents_router
from .api.routes.audit import router as audit_router
from .api.routes.auth import router as auth_router
from .api.routes.protocols import router as protocols_router
from .api.routes.studio import router as studio_router
from .api.routes.workflows import router as workflows_router
from .core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Starter API for hybrid AI document automation workflows.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents_router, prefix=settings.api_prefix)
app.include_router(workflows_router, prefix=settings.api_prefix)
app.include_router(audit_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(studio_router, prefix=settings.api_prefix)
app.include_router(protocols_router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "status": "running",
        "name": settings.app_name,
        "environment": settings.app_env,
        "docs": "/docs",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}
