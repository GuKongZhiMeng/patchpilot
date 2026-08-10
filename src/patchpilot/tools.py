"""Tool dispatcher for workspace operations and constrained subprocesses."""

from __future__ import annotations

import subprocess
from typing import Sequence

from .guardrails import ApprovalStore, Guardrail, PatchPilotError
from .workspace import Workspace


class ToolRegistry:
    def __init__(
        self,
        workspace: Workspace,
        guardrail: Guardrail,
        approval_store: ApprovalStore | None = None,
        *,
        command_timeout_seconds: int = 30,
        max_output_bytes: int = 16_384,
        check_commands: Sequence[Sequence[str]] = (),
    ) -> None:
        if command_timeout_seconds < 1 or max_output_bytes < 1:
            raise PatchPilotError("invalid_argument", "command limits must be positive")
        self.workspace = workspace
        self.guardrail = guardrail
        self.approval_store = approval_store or ApprovalStore()
        self.command_timeout_seconds = command_timeout_seconds
        self.max_output_bytes = max_output_bytes
        self.check_commands = tuple(tuple(command) for command in check_commands)

    def read_file(self, path: str) -> str:
        return self.workspace.read_file(path)

    def write_file(self, path: str, content: str) -> None:
        self.workspace.write_file(path, content)

    def run_command(self, argv: Sequence[str], approval_token: str | None = None) -> dict[str, object]:
        decision = self.guardrail.classify(argv)
        action = {"action": "run_command", "args": {"argv": list(argv)}}
        if decision == "deny":
            raise PatchPilotError("policy_denied", "command is prohibited by policy")
        if decision == "approval":
            if approval_token is None:
                raise PatchPilotError("approval_required", "command requires an approval token")
            self.approval_store.consume(approval_token, action)

        try:
            completed = subprocess.run(
                list(argv), cwd=self.workspace.root, shell=False, capture_output=True,
                timeout=self.command_timeout_seconds, check=False,
            )
            stdout, stderr, timed_out, returncode = completed.stdout, completed.stderr, False, completed.returncode
        except subprocess.TimeoutExpired as exc:
            stdout = exc.output or b""
            stderr = exc.stderr or b""
            timed_out, returncode = True, None
        except OSError as exc:
            raise PatchPilotError("command_failed", str(exc)) from exc

        stdout, stderr, truncated = self._bounded_output(stdout, stderr)
        return {
            "returncode": returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "timed_out": timed_out,
            "truncated": truncated,
        }

    def run_checks(self) -> list[dict[str, object]]:
        return [self.run_command(command) for command in self.check_commands]

    def _bounded_output(self, stdout: bytes, stderr: bytes) -> tuple[bytes, bytes, bool]:
        payload = stdout + stderr
        if len(payload) <= self.max_output_bytes:
            return stdout, stderr, False
        kept = payload[: self.max_output_bytes]
        return kept[: min(len(stdout), self.max_output_bytes)], kept[len(stdout) :], True
