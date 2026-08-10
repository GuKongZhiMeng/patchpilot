# T1 TDD evidence

- Red: bundled Python with `PYTHONPATH=src python -m unittest tests.test_config_llm -v` failed at import: `ModuleNotFoundError: patchpilot.config` (2026-08-10).
- Green: same command passed 8/8 tests (2026-08-10).
