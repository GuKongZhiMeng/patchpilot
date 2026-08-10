from __future__ import annotations

import os
from pathlib import Path

from .errors import PatchPilotError


class CredentialStore:
    SERVICE = "patchpilot"
    USER = "llm-api-key"

    def __init__(self, backend=None, secret_file: str | Path | None = None):
        self._backend = backend
        self.secret_file = Path(secret_file) if secret_file else None

    def _keyring(self):
        if self._backend is not None:
            return self._backend
        try:
            import keyring
        except ImportError as exc:
            raise PatchPilotError("keyring_unavailable", "Install PatchPilot with the secure extra or use a read-only secret file") from exc
        self._backend = keyring
        return keyring

    def get(self) -> str | None:
        if self.secret_file:
            if not self.secret_file.is_file():
                raise PatchPilotError("secret_file_missing", "Secret file does not exist")
            if os.name != "nt" and self.secret_file.stat().st_mode & 0o077:
                raise PatchPilotError("insecure_secret_file", "Secret file must not be accessible by group or others")
            value = self.secret_file.read_text(encoding="utf-8").strip()
            if not value:
                raise PatchPilotError("secret_file_empty", "Secret file is empty")
            return value
        return self._keyring().get_password(self.SERVICE, self.USER)

    def set(self, value: str) -> None:
        if self.secret_file:
            raise PatchPilotError("read_only_credentials", "Mounted secret files cannot be updated by PatchPilot")
        if not isinstance(value, str) or not value.strip():
            raise PatchPilotError("invalid_credential", "Key cannot be empty")
        self._keyring().set_password(self.SERVICE, self.USER, value.strip())

    def clear(self) -> None:
        if self.secret_file:
            raise PatchPilotError("read_only_credentials", "Remove the mounted secret outside PatchPilot")
        backend = self._keyring()
        if backend.get_password(self.SERVICE, self.USER) is not None:
            backend.delete_password(self.SERVICE, self.USER)

    def status(self) -> dict[str, object]:
        configured = self.get() is not None
        return {"configured": configured, "source": "secret-file" if self.secret_file else "os-keyring"}

