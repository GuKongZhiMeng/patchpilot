from __future__ import annotations

import argparse
import getpass
import json
from pathlib import Path

from .credentials import CredentialStore
from .config import Config
from .demo import run_demo
from .engine import AgentLoop
from .guardrails import Guardrail
from .llm import OpenAICompatibleLLM
from .memory import MemoryStore
from .tools import ToolRegistry
from .workspace import Workspace
from .web import serve


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="patchpilot")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo")
    run = sub.add_parser("run")
    run.add_argument("task"); run.add_argument("--workspace", default=".")
    run.add_argument("--base-url", default="https://api.openai.com/v1"); run.add_argument("--model", required=True)
    run.add_argument("--secret-file")
    web = sub.add_parser("serve"); web.add_argument("--host", default="127.0.0.1"); web.add_argument("--port", type=int, default=8765)
    key = sub.add_parser("key"); key.add_argument("action", choices=["status", "set", "clear"])
    args = parser.parse_args(argv)
    if args.command == "demo": print(json.dumps(run_demo(), ensure_ascii=False, indent=2)); return 0
    if args.command == "serve": serve(args.host, args.port); return 0
    if args.command == "run":
        root = Path(args.workspace).resolve(); cfg = Config()
        credentials = CredentialStore(secret_file=args.secret_file)
        api_key = credentials.get()
        if api_key is None:
            api_key = getpass.getpass("No key configured. API key (hidden): ")
            credentials.set(api_key)
        memory = MemoryStore(root / ".patchpilot.db")
        try:
            tools = ToolRegistry(
                Workspace(root, cfg.max_file_bytes), Guardrail(cfg.allowed_commands),
                command_timeout_seconds=cfg.command_timeout_seconds,
                max_output_bytes=cfg.max_output_bytes, check_commands=cfg.check_commands,
            )
            llm = OpenAICompatibleLLM(args.base_url, args.model, api_key, cfg.command_timeout_seconds)
            result = AgentLoop(llm, tools, cfg, memory).run(args.task, str(root))
            print(json.dumps(result.__dict__, ensure_ascii=False, indent=2)); return 0 if result.status == "completed" else 2
        finally:
            memory.close()
    store = CredentialStore()
    if args.action == "status": print(json.dumps(store.status())); return 0
    if args.action == "set": store.set(getpass.getpass("API key (hidden): ")); print("Key stored in OS keyring."); return 0
    store.clear(); print("Key cleared."); return 0


if __name__ == "__main__": raise SystemExit(main())
