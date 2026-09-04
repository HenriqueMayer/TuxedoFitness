"""Process-local storage for short-lived Hevy web credentials."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from time import time

from django.conf import settings


@dataclass(frozen=True, repr=False)
class _Credential:
    api_key: str
    user_id: int
    expires_at: float


class SessionCredentialStore:
    """Keep credentials in memory, isolated by authenticated Django session."""

    def __init__(self):
        self._credentials: dict[str, _Credential] = {}
        self._lock = RLock()

    @staticmethod
    def _session_key(request) -> str:
        if request.session.session_key is None:
            request.session.create()
        return request.session.session_key

    def put(self, request, api_key: str) -> None:
        key = self._session_key(request)
        credential = _Credential(
            api_key=api_key.strip(),
            user_id=request.user.pk,
            expires_at=time() + settings.SESSION_COOKIE_AGE,
        )
        with self._lock:
            self._prune_locked()
            self._credentials[key] = credential

    def get(self, request) -> str | None:
        key = request.session.session_key
        if not key:
            return None
        with self._lock:
            self._prune_locked()
            credential = self._credentials.get(key)
            if credential is None or credential.user_id != request.user.pk:
                return None
            return credential.api_key

    def delete(self, request) -> None:
        key = request.session.session_key
        if not key:
            return
        with self._lock:
            self._credentials.pop(key, None)

    def clear(self) -> None:
        """Test and process-shutdown helper."""
        with self._lock:
            self._credentials.clear()

    def _prune_locked(self) -> None:
        now = time()
        expired = [key for key, item in self._credentials.items() if item.expires_at <= now]
        for key in expired:
            self._credentials.pop(key, None)


session_credentials = SessionCredentialStore()
