from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from .config import Config
from .engine import AgentLoop
from .guardrails import Guardrail
from .llm import ScriptedLLM
from .memory import MemoryStore
from .tools import ToolRegistry
from .workspace import Workspace


def _action(name: str, **args) -> str:
    return json.dumps({"action": name, "args": args})


def run_demo(task: str = "repair a failing unit test") -> dict[str, object]:
    guardrail = Guardrail([Path(sys.executable).name])
    blocked = guardrail.classify(["rm", "-rf", "/"]) == "deny"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cfg = Config.from_mapping({
            "allowed_commands": [Path(sys.executable).name],
            "check_commands": [[sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test_demo.py"]],
            "repeat_failure_limit": 2,
        })
        tools = ToolRegistry(Workspace(root), guardrail, check_commands=cfg.check_commands)
        memory = MemoryStore(root / "events.db")
        failing = "import unittest\nclass D(unittest.TestCase):\n def test_demo(self): self.assertEqual(1,2)\n"
        repaired = "import unittest\nclass D(unittest.TestCase):\n def test_demo(self):\n  # fixed\n  self.assertEqual(1,1)\n"
        llm = ScriptedLLM([
            _action("write_file", path="test_demo.py", content=failing),
            _action("write_file", path="test_demo.py", content=repaired),
            _action("finish", summary="tests pass"),
        ])
        repaired_result = AgentLoop(llm, tools, cfg, memory).run(task, "demo")
        repaired_events = memory.events(repaired_result.run_id)
        root.joinpath("__pycache__").mkdir(exist_ok=True)
        stalled_llm = ScriptedLLM([
            _action("write_file", path="test_demo.py", content=failing),
            _action("write_file", path="test_demo.py", content=failing),
        ])
        stalled_result = AgentLoop(stalled_llm, tools, cfg, memory).run(task, "demo")
        memory.close()
    return {
        "task": task,
        "guardrail": "blocked" if blocked else "unsafe",
        "feedback_loop": "repaired" if repaired_result.status == "completed" and len(llm.calls) == 3 else repaired_result.status,
        "deep_mechanism": "stalled_on_repeat" if stalled_result.status == "stalled" else stalled_result.status,
        "feedback_seen": "feedback" in llm.calls[1][-1]["content"],
        "action_changed": failing != repaired,
        "workspace": "ephemeral-temp",
        "events": repaired_events,
    }
