from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Mapping, Any

from .errors import PatchPilotError


@dataclass(frozen=True)
class Config:
    max_steps: int = 12
    command_timeout_seconds: int = 30
    max_output_bytes: int = 16384
    max_file_bytes: int = 1048576
    allowed_commands: tuple[str, ...] = ("python", "python3", "pytest", "git")
    check_commands: tuple[tuple[str, ...], ...] = (("python", "-m", "unittest", "discover", "-s", "tests"),)
    repeat_failure_limit: int = 2
    repair_budget: int = 4
    memory_limit: int = 5
    bind_host: str = "127.0.0.1"
    bind_port: int = 8765

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None = None) -> "Config":
        data = dict(data or {})
        known = {f.name for f in fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise PatchPilotError("unknown_config", f"Unknown config: {', '.join(sorted(unknown))}")
        try:
            if "allowed_commands" in data:
                value = data["allowed_commands"]
                if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
                    raise ValueError
                data["allowed_commands"] = tuple(value)
            if "check_commands" in data:
                value = data["check_commands"]
                if not isinstance(value, list) or not all(isinstance(v, list) and v and all(isinstance(x, str) for x in v) for v in value):
                    raise ValueError
                data["check_commands"] = tuple(tuple(v) for v in value)
            cfg = cls(**data)
        except (TypeError, ValueError) as exc:
            raise PatchPilotError("invalid_config", "Invalid config value") from exc
        ranges = {
            "max_steps": (1, 100), "command_timeout_seconds": (1, 300),
            "max_output_bytes": (1024, 1048576), "max_file_bytes": (1024, 10485760),
            "repeat_failure_limit": (1, 10), "repair_budget": (0, 20),
            "memory_limit": (0, 50), "bind_port": (1, 65535),
        }
        for name, (low, high) in ranges.items():
            value = getattr(cfg, name)
            if type(value) is not int or not low <= value <= high:
                raise PatchPilotError("invalid_config", f"{name} outside allowed range")
        if not isinstance(cfg.bind_host, str):
            raise PatchPilotError("invalid_config", "bind_host must be a string")
        return cfg

