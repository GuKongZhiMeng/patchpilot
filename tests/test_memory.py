import tempfile
import unittest
from pathlib import Path

from patchpilot.errors import PatchPilotError
from patchpilot.memory import MemoryStore


class MemoryStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = MemoryStore(Path(self.tmp.name) / "memory.db")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_workspace_isolation_and_relevance_limit(self):
        self.store.add("a", "convention", "use unittest for Python tests")
        self.store.add("a", "decision", "serve the web interface locally")
        self.store.add("b", "convention", "use pytest only")
        found = self.store.search("a", "python unittest", limit=1)
        self.assertEqual(len(found), 1)
        self.assertIn("unittest", found[0].text)
        self.assertNotIn("pytest", found[0].text)

    def test_rejects_secret_like_memory(self):
        with self.assertRaises(PatchPilotError) as caught:
            self.store.add("a", "decision", "api_key=sk-super-secret")
        self.assertEqual(caught.exception.code, "sensitive_memory")

    def test_events_round_trip(self):
        self.store.record_event("run-1", 2, "tool_result", {"ok": True})
        events = self.store.events("run-1")
        self.assertEqual(events[0]["payload"], {"ok": True})


if __name__ == "__main__": unittest.main()
