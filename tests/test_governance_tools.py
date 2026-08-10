"""Offline TDD coverage for workspace containment and command governance."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from patchpilot.guardrails import ApprovalStore, Guardrail
from patchpilot.tools import ToolRegistry
from patchpilot.workspace import Workspace


class WorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "workspace"
        self.root.mkdir()
        self.workspace = Workspace(self.root, max_file_bytes=64)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_rejects_traversal_absolute_and_external_symlink(self) -> None:
        for value in ("../outside.txt", str(self.root / "absolute.txt")):
            with self.assertRaises(Exception) as caught:
                self.workspace.resolve(value)
            self.assertEqual(caught.exception.code, "path_outside_workspace")

        outside = self.root.parent / "patchpilot-outside.txt"
        outside.write_text("no", encoding="utf-8")
        link = self.root / "link.txt"
        try:
            link.symlink_to(outside)
        except OSError:
            self.skipTest("symbolic links unavailable on this Windows host")
        with self.assertRaises(Exception) as caught:
            self.workspace.read_file("link.txt")
        self.assertEqual(caught.exception.code, "path_outside_workspace")

    def test_atomic_write_creates_parents_and_replaces_content(self) -> None:
        self.workspace.write_file("nested/note.txt", "first")
        self.workspace.write_file("nested/note.txt", "second")
        self.assertEqual("second", self.workspace.read_file("nested/note.txt"))
        self.assertFalse(list((self.root / "nested").glob("*.tmp")))


class GuardrailTests(unittest.TestCase):
    def setUp(self) -> None:
        self.guardrail = Guardrail(["python", "git", "docker"])

    def test_denies_dangerous_commands_and_shell_interpreters(self) -> None:
        for argv in (["rm", "-rf", "/"], ["cmd", "/c", "echo hi"], ["powershell", "-Command", "dir"], ["python", "-c", "print(1)"], ["git", "-C", "../outside", "status"]):
            self.assertEqual("deny", self.guardrail.classify(argv))

    def test_requires_single_use_approval_for_publish(self) -> None:
        action = {"action": "run_command", "args": {"argv": ["git", "push"]}}
        self.assertEqual("approval", self.guardrail.classify(["git", "push"]))
        store = ApprovalStore(now=lambda: 100.0, token_factory=lambda: "token")
        token = store.issue(action, ttl_seconds=60)
        self.assertTrue(store.consume(token, action))
        with self.assertRaises(Exception) as caught:
            store.consume(token, action)
        self.assertEqual(caught.exception.code, "approval_replayed")

    def test_allows_whitelisted_command_only(self) -> None:
        self.assertEqual("allow", self.guardrail.classify(["python", "-V"]))
        self.assertEqual("deny", self.guardrail.classify(["curl", "example.test"]))


class ToolRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        executable = Path(sys.executable)
        self.tools = ToolRegistry(
            Workspace(Path(self.tmp.name), max_file_bytes=128),
            Guardrail([executable.name]),
            command_timeout_seconds=5,
            max_output_bytes=32,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_runs_allowed_command_without_a_shell_and_truncates_output(self) -> None:
        result = self.tools.run_command([sys.executable, "-m", "unittest", "--help"])
        self.assertEqual(0, result["returncode"])
        self.assertTrue(result["truncated"])
        self.assertLessEqual(len(result["stdout"].encode("utf-8")), 32)


if __name__ == "__main__":
    unittest.main()
