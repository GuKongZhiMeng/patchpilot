import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from patchpilot.config import Config
from patchpilot.errors import PatchPilotError
from patchpilot.llm import OpenAICompatibleLLM, ScriptedLLM
from patchpilot.models import Action


class ActionTests(unittest.TestCase):
    def test_parses_write_action(self):
        action = Action.from_json('{"action":"write_file","args":{"path":"a.py","content":"x"}}')
        self.assertEqual(action.name, "write_file")
        self.assertEqual(action.args["path"], "a.py")

    def test_rejects_unknown_and_extra_fields(self):
        for raw, code in [
            ('{"action":"launch","args":{}}', "unknown_action"),
            ('{"action":"finish","args":{"summary":"ok","extra":1}}', "invalid_argument"),
            ("not json", "invalid_json"),
        ]:
            with self.subTest(raw=raw), self.assertRaises(PatchPilotError) as caught:
                Action.from_json(raw)
            self.assertEqual(caught.exception.code, code)

    def test_requires_argv_as_string_list(self):
        with self.assertRaises(PatchPilotError) as caught:
            Action.from_json('{"action":"run_command","args":{"argv":"pytest"}}')
        self.assertEqual(caught.exception.code, "invalid_argument")


class ConfigTests(unittest.TestCase):
    def test_defaults_and_override(self):
        cfg = Config.from_mapping({"max_steps": 3, "allowed_commands": ["python"]})
        self.assertEqual(cfg.max_steps, 3)
        self.assertEqual(cfg.bind_host, "127.0.0.1")
        self.assertEqual(cfg.allowed_commands, ("python",))

    def test_unknown_and_out_of_range_rejected(self):
        for data, code in [({"wat": 1}, "unknown_config"), ({"max_steps": 0}, "invalid_config")]:
            with self.subTest(data=data), self.assertRaises(PatchPilotError) as caught:
                Config.from_mapping(data)
            self.assertEqual(caught.exception.code, code)


class ScriptedLLMTests(unittest.TestCase):
    def test_records_deep_copy_and_exhausts(self):
        llm = ScriptedLLM(['{"action":"finish","args":{"summary":"ok"}}'])
        messages = [{"role": "user", "content": "task"}]
        self.assertIn("finish", llm.complete(messages))
        messages[0]["content"] = "mutated"
        self.assertEqual(llm.calls[0][0]["content"], "task")
        with self.assertRaises(PatchPilotError) as caught:
            llm.complete(messages)
        self.assertEqual(caught.exception.code, "llm_script_exhausted")


class _Handler(BaseHTTPRequestHandler):
    response_body = b'{"choices":[{"message":{"content":"ok"}}]}'
    request_body = b""
    authorization = ""

    def do_POST(self):
        type(self).request_body = self.rfile.read(int(self.headers["Content-Length"]))
        type(self).authorization = self.headers.get("Authorization", "")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(type(self).response_body)

    def log_message(self, *_args):
        pass


class HTTPAdapterTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_sends_protocol_and_parses_content(self):
        base = f"http://127.0.0.1:{self.server.server_port}"
        llm = OpenAICompatibleLLM(base, "test-model", "secret", 2)
        value = llm.complete([{"role": "user", "content": "hi"}])
        self.assertEqual(value, "ok")
        body = json.loads(_Handler.request_body)
        self.assertEqual(body["temperature"], 0)
        self.assertEqual(_Handler.authorization, "Bearer secret")

    def test_rejects_invalid_response_schema(self):
        _Handler.response_body = b'{"choices":[]}'
        base = f"http://127.0.0.1:{self.server.server_port}"
        with self.assertRaises(PatchPilotError) as caught:
            OpenAICompatibleLLM(base, "m", "k", 2).complete([])
        self.assertEqual(caught.exception.code, "llm_invalid_response")
        _Handler.response_body = b'{"choices":[{"message":{"content":"ok"}}]}'


if __name__ == "__main__":
    unittest.main()
