import json
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock

from ..core.schemas import CredentialCreateRequest, CredentialRecord


class CredentialStore:
    def __init__(self, store_path: str) -> None:
        self._path = Path(store_path)
        self._lock = Lock()
        self._cache: dict[str, dict[str, str | list[str]]] = {}
        self._load()

    def list_records(self) -> list[CredentialRecord]:
        with self._lock:
            return [
                CredentialRecord(
                    alias=alias,
                    scope=str(payload["scope"]),
                    integrations=list(payload.get("integrations", [])),
                    masked_value=self._mask(str(payload["secret_value"])),
                    created_at=datetime.fromisoformat(str(payload["created_at"])),
                )
                for alias, payload in sorted(self._cache.items())
            ]

    def create(self, request: CredentialCreateRequest) -> CredentialRecord:
        with self._lock:
            payload = {
                "scope": request.scope,
                "secret_value": request.secret_value,
                "integrations": request.integrations,
                "created_at": datetime.now(UTC).isoformat(),
            }
            self._cache[request.alias] = payload
            self._persist()
            return CredentialRecord(
                alias=request.alias,
                scope=request.scope,
                integrations=request.integrations,
                masked_value=self._mask(request.secret_value),
                created_at=datetime.fromisoformat(str(payload["created_at"])),
            )

    def resolve(self, alias: str | None) -> str | None:
        if not alias:
            return None
        with self._lock:
            payload = self._cache.get(alias)
            if not payload:
                return None
            return str(payload["secret_value"])

    def has_scope(self, alias: str | None, scope: str) -> bool:
        if not alias:
            return False
        with self._lock:
            payload = self._cache.get(alias)
            if not payload:
                return False
            return str(payload["scope"]) == scope

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raw = {}
        if isinstance(raw, dict):
            self._cache = raw

    def _persist(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._cache, indent=2), encoding="utf-8")

    @staticmethod
    def _mask(secret_value: str) -> str:
        if len(secret_value) <= 4:
            return "*" * len(secret_value)
        return f"{secret_value[:2]}{'*' * (len(secret_value) - 4)}{secret_value[-2:]}"
