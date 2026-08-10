import json
import os
import tempfile
import threading
import unittest
import urllib.request
from importlib.resources import files
from pathlib import Path

from patchpilot.credentials import CredentialStore
from patchpilot.demo import run_demo
from patchpilot.errors import PatchPilotError
from patchpilot.web import create_server


class FakeBackend:
    def __init__(self): self.value = None
    def get_password(self, service, user): return self.value
    def set_password(self, service, user, value): self.value = value
    def delete_password(self, service, user): self.value = None


class CredentialTests(unittest.TestCase):
    def test_key_lifecycle_never_returns_plaintext_status(self):
        backend = FakeBackend(); store = CredentialStore(backend=backend)
        store.set("sk-test-secret")
        self.assertEqual(store.status(), {"configured": True, "source": "os-keyring"})
        self.assertEqual(store.get(), "sk-test-secret")
        store.clear(); self.assertFalse(store.status()["configured"])

    @unittest.skipIf(os.name == "nt", "POSIX permission bits are not authoritative on Windows")
    def test_rejects_world_readable_secret_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "secret"; path.write_text("secret", encoding="utf-8"); path.chmod(0o644)
            with self.assertRaises(PatchPilotError) as caught: CredentialStore(secret_file=path).get()
            self.assertEqual(caught.exception.code, "insecure_secret_file")


class DemoTests(unittest.TestCase):
    def test_demo_replays_required_mechanisms(self):
        result = run_demo()
        self.assertEqual(result["guardrail"], "blocked")
        self.assertEqual(result["feedback_loop"], "repaired")
        self.assertEqual(result["deep_mechanism"], "stalled_on_repeat")
        self.assertTrue(result["feedback_seen"])
        self.assertTrue(result["action_changed"])
        self.assertEqual(result["workspace"], "ephemeral-temp")
        self.assertGreaterEqual(len(result["events"]), 3)


class WebTests(unittest.TestCase):
    def test_page_has_structured_workspace_safety_and_timeline(self):
        html = files("patchpilot.static").joinpath("index.html").read_text(encoding="utf-8")
        for marker in ('id="workspace"', 'id="safety"', 'id="events"'):
            self.assertIn(marker, html)

    def test_health_and_security_headers(self):
        server = create_server("127.0.0.1", 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}/healthz") as response:
                body = json.load(response)
                self.assertEqual(body, {"status": "ok"})
                self.assertIn("default-src", response.headers["Content-Security-Policy"])
        finally:
            server.shutdown(); server.server_close()


if __name__ == "__main__": unittest.main()
