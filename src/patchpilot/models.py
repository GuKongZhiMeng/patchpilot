from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .errors import PatchPilotError


_SCHEMAS: dict[str, dict[str, object]] = {
    "read_file": {"path": str},
    "write_file": {"path": str, "content": str},
    "run_command": {"argv": list},
    "run_checks": {},
    "remember": {"kind": str, "text": str},
    "finish": {"summary": str},
}


@dataclass(frozen=True)
class Action:
    name: str
    args: dict[str, Any]

    @classmethod
    def from_json(cls, text: str) -> "Action":
        try:
            raw = json.loads(text)
        except (json.JSONDecodeError, TypeError) as exc:
            raise PatchPilotError("invalid_json", "LLM output is not valid JSON") from exc
        if not isinstance(raw, dict) or set(raw) != {"action", "args"}:
            raise PatchPilotError("invalid_action", "Action must contain only action and args")
        name, args = raw["action"], raw["args"]
        if not isinstance(name, str) or not isinstance(args, dict):
            raise PatchPilotError("invalid_action", "Invalid action envelope")
        if name not in _SCHEMAS:
            raise PatchPilotError("unknown_action", f"Unknown action: {name}")
        schema = _SCHEMAS[name]
        missing = set(schema) - set(args)
        if missing:
            raise PatchPilotError("missing_argument", f"Missing: {', '.join(sorted(missing))}")
        if set(args) != set(schema):
            raise PatchPilotError("invalid_argument", "Action contains unknown arguments")
        for key, expected in schema.items():
            value = args[key]
            if not isinstance(value, expected):
                raise PatchPilotError("invalid_argument", f"Invalid type for {key}")
        if name == "run_command" and (not args["argv"] or not all(isinstance(v, str) and v for v in args["argv"])):
            raise PatchPilotError("invalid_argument", "argv must be a non-empty list of strings")
        if name == "remember" and args["kind"] not in {"convention", "decision", "failure"}:
            raise PatchPilotError("invalid_argument", "Invalid memory kind")
        return cls(name=name, args=dict(args))

    def canonical_json(self) -> str:
        return json.dumps({"action": self.name, "args": self.args}, sort_keys=True, separators=(",", ":"))

