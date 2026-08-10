# T5 TDD evidence

- Red: import failed with `ModuleNotFoundError: patchpilot.engine` (2026-08-10).
- Green: after making the fixture invalidate Python bytecode deterministically, 4/4 tests passed. The transient same-size/same-second rewrite exposed a real test-fixture cache hazard and was corrected (2026-08-10).
