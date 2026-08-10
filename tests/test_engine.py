import json
import sys
import tempfile
import unittest
from pathlib import Path

from patchpilot.config import Config
from patchpilot.engine import AgentLoop
from patchpilot.guardrails import Guardrail
from patchpilot.guardrails import ApprovalStore
from patchpilot.llm import ScriptedLLM
from patchpilot.memory import MemoryStore
from patchpilot.tools import ToolRegistry
from patchpilot.workspace import Workspace


def action(name, **args):
    return json.dumps({"action": name, "args": args})


class AgentLoopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "test_generated.py").write_text(
            "import unittest\nclass Baseline(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n",
            encoding="utf-8",
        )
        self.memory = MemoryStore(root / "memory.db")
        exe = Path(sys.executable).name
        self.config = Config.from_mapping({
            "allowed_commands": [exe],
            "check_commands": [[sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test_generated.py"]],
            "repeat_failure_limit": 2,
            "repair_budget": 3,
        })
        self.tools = ToolRegistry(
            Workspace(root, self.config.max_file_bytes), Guardrail(self.config.allowed_commands),
            command_timeout_seconds=5, max_output_bytes=self.config.max_output_bytes,
            check_commands=self.config.check_commands,
        )

    def tearDown(self):
        self.memory.close(); self.tmp.cleanup()

    def test_failure_feedback_changes_next_action_and_finishes(self):
        llm = ScriptedLLM([
            action("write_file", path="test_generated.py", content="import unittest\nclass T(unittest.TestCase):\n def test_x(self): self.assertEqual(1, 2)\n"),
            action("write_file", path="test_generated.py", content="import unittest\nclass T(unittest.TestCase):\n def test_x(self):\n  # repaired\n  self.assertEqual(1, 1)\n"),
            action("finish", summary="fixed"),
        ])
        result = AgentLoop(llm, self.tools, self.config, self.memory).run("make tests pass", "ws")
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.summary, "fixed")
        self.assertIn("test_assertion", llm.calls[1][-1]["content"])

    def test_guardrail_error_is_fed_back_without_execution(self):
        llm = ScriptedLLM([action("run_command", argv=["rm", "-rf", "/"]), action("finish", summary="safe")])
        result = AgentLoop(llm, self.tools, self.config, self.memory).run("delete", "ws")
        self.assertEqual(result.status, "completed")
        self.assertIn("policy_denied", llm.calls[1][-1]["content"])

    def test_repeated_identical_failure_stalls(self):
        failing = action("write_file", path="test_generated.py", content="this is invalid python")
        llm = ScriptedLLM([failing, failing, action("finish", summary="unreachable")])
        result = AgentLoop(llm, self.tools, self.config, self.memory).run("fix", "ws")
        self.assertEqual(result.status, "stalled")
        self.assertEqual(len(llm.calls), 2)

    def test_invalid_action_becomes_observation(self):
        llm = ScriptedLLM(["not json", action("finish", summary="done")])
        result = AgentLoop(llm, self.tools, self.config, self.memory).run("noop", "ws")
        self.assertEqual(result.status, "completed")
        self.assertIn("invalid_json", llm.calls[1][-1]["content"])

    def test_publish_pauses_without_callback(self):
        class FakeTools:
            guardrail = Guardrail(["git"])
            approval_store = ApprovalStore()
            def run_checks(self): return []
        llm = ScriptedLLM([action("run_command", argv=["git", "push"])])
        result = AgentLoop(llm, FakeTools(), self.config, self.memory).run("publish", "ws")
        self.assertEqual(result.status, "awaiting_approval")
        self.assertEqual(len(llm.calls), 1)

    def test_publish_executes_after_callback_approval(self):
        class FakeTools:
            guardrail = Guardrail(["git"])
            approval_store = ApprovalStore(token_factory=lambda: "approved")
            def run_checks(self): return []
            def run_command(self, argv, approval_token=None):
                self.seen = (argv, approval_token)
                self.approval_store.consume(approval_token, {"action":"run_command","args":{"argv":argv}})
                return {"returncode":0,"stdout":"","stderr":"","timed_out":False,"truncated":False}
        fake = FakeTools(); llm = ScriptedLLM([action("run_command", argv=["git", "push"]), action("finish", summary="published")])
        loop = AgentLoop(llm, fake, self.config, self.memory, approval_callback=lambda _action: True)
        result = loop.run("publish", "ws")
        self.assertEqual(result.status, "completed")
        self.assertEqual(fake.seen, (["git", "push"], "approved"))


if __name__ == "__main__": unittest.main()
