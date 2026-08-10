"""Constrained, UTF-8 workspace file access."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path, PurePosixPath, PureWindowsPath

from .guardrails import PatchPilotError


class Workspace:
    """Expose files beneath one resolved workspace root only."""

    def __init__(self, root: str | Path, max_file_bytes: int = 1_048_576) -> None:
        if not isinstance(max_file_bytes, int) or max_file_bytes < 1:
            raise PatchPilotError("invalid_argument", "max_file_bytes must be a positive integer")
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise PatchPilotError("invalid_argument", "workspace root must be a directory")
        self.max_file_bytes = max_file_bytes

    def resolve(self, relative_path: str) -> Path:
        """Return an in-root path, rejecting traversal and reparse-point escapes."""
        if not isinstance(relative_path, str) or not relative_path:
            raise PatchPilotError("invalid_argument", "path must be a non-empty string")
        if PureWindowsPath(relative_path).is_absolute() or PurePosixPath(relative_path).is_absolute():
            raise PatchPilotError("path_outside_workspace", "absolute paths are not allowed")
        if ".." in PureWindowsPath(relative_path).parts or ".." in PurePosixPath(relative_path).parts:
            raise PatchPilotError("path_outside_workspace", "path traversal is not allowed")

        candidate = (self.root / Path(relative_path)).resolve(strict=False)
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise PatchPilotError("path_outside_workspace", "path resolves outside workspace") from exc
        return candidate

    def read_file(self, relative_path: str) -> str:
        path = self.resolve(relative_path)
        if not path.exists():
            raise PatchPilotError("file_not_found", "file does not exist")
        if not path.is_file():
            raise PatchPilotError("invalid_file", "path is not a regular file")
        data = path.read_bytes()
        if len(data) > self.max_file_bytes:
            raise PatchPilotError("file_too_large", "file exceeds configured read limit")
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PatchPilotError("invalid_utf8", "file is not UTF-8 text") from exc

    def write_file(self, relative_path: str, content: str) -> None:
        if not isinstance(content, str):
            raise PatchPilotError("invalid_argument", "content must be a string")
        data = content.encode("utf-8")
        if len(data) > self.max_file_bytes:
            raise PatchPilotError("file_too_large", "content exceeds configured write limit")

        path = self.resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Check again after mkdir: an existing/replaced parent may be a junction.
        path = self.resolve(relative_path)
        if path.exists() and path.is_dir():
            raise PatchPilotError("invalid_file", "cannot replace a directory")

        descriptor, temporary = tempfile.mkstemp(prefix=".patchpilot-", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        except Exception:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise
