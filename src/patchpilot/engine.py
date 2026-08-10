from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from typing import Any

from .config import Config
from .errors import PatchPilotError
from .feedback import Feedback, FeedbackLoop
from .llm import LLMPort
from .memory import MemoryStore
from .models import Action
from .tools import ToolRegistry


@dataclass(frozen=True)
class RunResult:
    run_id: str
    status: str
    summary: str
    steps: int


class AgentLoop:
    """Owns the complete decision/tool/feedback/stop loop."""

    def __init__(self, llm: LLMPort, tools: ToolRegistry, config: Config, memory: MemoryStore, approval_callback=None):
        self.llm, self.tools, self.config, self.memory = llm, tools, config, memory
        self.approval_callback = approval_callback

    def run(self, task: str, workspace_id: str) -> RunResult:
        run_id = uuid.uuid4().hex
        memories = self.memory.search(workspace_id, task, self.config.memory_limit)
        context = "\n".join(f"- [{m.kind}] {m.text}" for m in memories) or "(none)"
        messages = [
            {"role": "system", "content": "Return exactly one PatchPilot v1 JSON action. Safety and validation are enforced by code."},
            {"role": "user", "content": f"Task: {task}\nRelevant memory:\n{context}"},
        ]
        feedback_loop = FeedbackLoop(self.config.repeat_failure_limit, self.config.max_output_bytes)
        repairs = 0
        for step in range(1, self.config.max_steps + 1):
            raw = None
            try:
                raw = self.llm.complete(messages)
                action = Action.from_json(raw)
                self._event(run_id, step, "action", {"name": action.name})
                if action.name == "finish":
                    feedback = self._validate(feedback_loop)
                    if feedback.passed:
                        return RunResult(run_id, "completed", action.args["summary"], step)
                    repairs += 1
                    outcome = self._feedback_payload(feedback)
                else:
                    outcome, feedback = self._dispatch(action, workspace_id, feedback_loop)
                    if feedback is not None and not feedback.passed:
                        repairs += 1
                        if feedback.stalled:
                            return RunResult(run_id, "stalled", "Repeated identical validation failure", step)
                if repairs > self.config.repair_budget:
                    return RunResult(run_id, "budget_exhausted", "Repair budget exhausted", step)
            except PatchPilotError as exc:
                if exc.code in {"approval_required", "approval_denied"}:
                    return RunResult(run_id, "awaiting_approval" if exc.code == "approval_required" else "approval_denied", str(exc), step)
                outcome = {"ok": False, "error": {"code": exc.code, "message": str(exc)}}
                self._event(run_id, step, "error", {"code": exc.code})
            if raw is not None:
                messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": json.dumps({"observation": outcome}, ensure_ascii=False, sort_keys=True)})
        return RunResult(run_id, "step_limit", "Maximum steps reached", self.config.max_steps)

    def _dispatch(self, action: Action, workspace_id: str, loop: FeedbackLoop) -> tuple[dict[str, Any], Feedback | None]:
        a = action.args
        if action.name == "read_file":
            return {"ok": True, "content": self.tools.read_file(a["path"])}, None
        if action.name == "write_file":
            self.tools.write_file(a["path"], a["content"])
            feedback = self._validate(loop)
            return self._feedback_payload(feedback), feedback
        if action.name == "run_command":
            token = None
            if self.tools.guardrail.classify(a["argv"]) == "approval":
                if self.approval_callback is None:
                    raise PatchPilotError("approval_required", "Action paused for human approval")
                if not self.approval_callback(action):
                    raise PatchPilotError("approval_denied", "Human denied the action")
                token = self.tools.approval_store.issue({"action": "run_command", "args": {"argv": a["argv"]}}, 60)
            result = self.tools.run_command(a["argv"], approval_token=token)
            return {"ok": result["returncode"] == 0, "command": result}, None
        if action.name == "run_checks":
            feedback = self._validate(loop)
            return self._feedback_payload(feedback), feedback
        if action.name == "remember":
            self.memory.add(workspace_id, a["kind"], a["text"])
            return {"ok": True}, None
        raise PatchPilotError("unknown_action", action.name)

    def _validate(self, loop: FeedbackLoop) -> Feedback:
        results = self.tools.run_checks()
        if not results:
            return loop.record(exit_code=0, stdout="No checks configured")
        failed = next((r for r in results if r["returncode"] != 0 or r["timed_out"]), None)
        if failed is None:
            return loop.record(exit_code=0, stdout="All checks passed")
        return loop.record(
            exit_code=int(failed["returncode"] if failed["returncode"] is not None else 1),
            stdout=str(failed["stdout"]), stderr=str(failed["stderr"]), timed_out=bool(failed["timed_out"]),
        )

    @staticmethod
    def _feedback_payload(feedback: Feedback) -> dict[str, Any]:
        data = asdict(feedback)
        if feedback.category is not None:
            data["category"] = feedback.category.value
        return {"ok": feedback.passed, "feedback": data}

    def _event(self, run_id: str, step: int, kind: str, payload: dict[str, Any]) -> None:
        self.memory.record_event(run_id, step, kind, payload)
