from __future__ import annotations

import copy
import json
import urllib.error
import urllib.request
from typing import Protocol

from .errors import PatchPilotError


class LLMPort(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str: ...


class ScriptedLLM:
    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.calls: list[list[dict[str, str]]] = []

    def complete(self, messages: list[dict[str, str]]) -> str:
        self.calls.append(copy.deepcopy(messages))
        if not self._responses:
            raise PatchPilotError("llm_script_exhausted", "Scripted LLM has no responses left")
        return self._responses.pop(0)


class OpenAICompatibleLLM:
    def __init__(self, base_url: str, model: str, api_key: str, timeout_seconds: int = 30):
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def complete(self, messages: list[dict[str, str]]) -> str:
        payload = json.dumps({"model": self.model, "messages": messages, "temperature": 0}).encode()
        request = urllib.request.Request(self.url, data=payload, method="POST", headers={
            "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"
        })
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raise PatchPilotError("llm_http_error", f"LLM HTTP status {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise PatchPilotError("llm_network_error", "LLM network request failed") from exc
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise PatchPilotError("llm_invalid_json", "LLM returned invalid JSON") from exc
        try:
            choices = data["choices"]
            content = choices[0]["message"]["content"]
            if not isinstance(choices, list) or not choices or not isinstance(content, str):
                raise TypeError
        except (KeyError, IndexError, TypeError):
            raise PatchPilotError("llm_invalid_response", "LLM response schema is invalid")
        return content
