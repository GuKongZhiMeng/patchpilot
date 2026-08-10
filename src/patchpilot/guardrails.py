"""Deterministic command policy and one-time approval tokens."""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from pathlib import Path, PureWindowsPath
from typing import Any, Callable, Mapping, Sequence

try:  # T1 supplies the public shared error type when present.
    from .models import PatchPilotError
except ImportError:  # Keep this task independently testable before T1 merges.
    class PatchPilotError(Exception):
        def __init__(self, code: str, message: str) -> None:
            self.code = code
            self.message = message
            super().__init__(f"{code}: {message}")


def _program_name(value: str) -> str:
    return PureWindowsPath(value).name.lower() if "\\" in value else Path(value).name.lower()


class Guardrail:
    """Classify argv commands as allow, deny, or requiring approval."""

    _SHELLS = frozenset({"sh", "bash", "zsh", "fish", "cmd", "powershell", "pwsh"})
    _METACHARACTERS = frozenset("|&;<>`$")

    def __init__(self, allowed_commands: Sequence[str]) -> None:
        if isinstance(allowed_commands, (str, bytes)):
            raise PatchPilotError("invalid_argument", "allowed_commands must be a list")
        self.allowed_commands = frozenset(_program_name(item) for item in allowed_commands if isinstance(item, str))
        if len(self.allowed_commands) != len(allowed_commands) or not self.allowed_commands:
            raise PatchPilotError("invalid_argument", "allowed_commands must contain non-empty strings")

    def classify(self, argv: Sequence[str]) -> str:
        self._validate_argv(argv)
        program = _program_name(argv[0])
        lower_args = [item.lower() for item in argv[1:]]

        if program in self._SHELLS or any(char in item for item in argv for char in self._METACHARACTERS):
            return "deny"
        if program in {"rm", "del", "erase", "format", "diskpart", "sudo", "runas"}:
            return "deny"
        if program == "rmdir" and any(item in {"/s", "-r", "-rf", "/q"} for item in lower_args):
            return "deny"
        if program not in self.allowed_commands:
            return "deny"
        if (program == "git" and ("push" in lower_args or ("reset" in lower_args and "--hard" in lower_args))):
            return "approval"
        if (program == "docker" and "push" in lower_args) or (program == "npm" and "publish" in lower_args):
            return "approval"
        return "allow"

    @staticmethod
    def _validate_argv(argv: Sequence[str]) -> None:
        if isinstance(argv, (str, bytes)) or not isinstance(argv, Sequence) or not argv:
            raise PatchPilotError("invalid_argument", "argv must be a non-empty list of strings")
        if any(not isinstance(item, str) or not item for item in argv):
            raise PatchPilotError("invalid_argument", "argv must be a non-empty list of strings")


class ApprovalStore:
    """In-memory, content-bound, expiring, single-use approval tokens."""

    def __init__(
        self,
        now: Callable[[], float] | None = None,
        token_factory: Callable[[], str] | None = None,
    ) -> None:
        self._now = now or time.time
        self._token_factory = token_factory or (lambda: secrets.token_urlsafe(32))
        self._tokens: dict[str, tuple[str, float, bool]] = {}

    @staticmethod
    def _digest(action: Mapping[str, Any]) -> str:
        if not isinstance(action, Mapping):
            raise PatchPilotError("invalid_argument", "approval action must be an object")
        try:
            canonical = json.dumps(action, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            raise PatchPilotError("invalid_argument", "approval action must be JSON serializable") from exc
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def issue(self, action: Mapping[str, Any], ttl_seconds: int = 60) -> str:
        if not isinstance(ttl_seconds, (int, float)) or ttl_seconds <= 0:
            raise PatchPilotError("invalid_argument", "approval TTL must be positive")
        token = self._token_factory()
        if not isinstance(token, str) or not token:
            raise PatchPilotError("invalid_argument", "token factory returned an invalid token")
        self._tokens[token] = (self._digest(action), self._now() + ttl_seconds, False)
        return token

    def consume(self, token: str, action: Mapping[str, Any]) -> bool:
        if not isinstance(token, str) or token not in self._tokens:
            raise PatchPilotError("approval_invalid", "approval token is invalid")
        digest, expires_at, used = self._tokens[token]
        if used:
            raise PatchPilotError("approval_replayed", "approval token was already used")
        if self._now() >= expires_at:
            raise PatchPilotError("approval_expired", "approval token has expired")
        if not secrets.compare_digest(digest, self._digest(action)):
            raise PatchPilotError("approval_invalid", "approval token does not match action")
        self._tokens[token] = (digest, expires_at, True)
        return True
