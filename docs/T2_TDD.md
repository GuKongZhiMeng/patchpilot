# T2 TDD record

The governance-tool tests are fully offline: temporary directories, the Python
standard library, and the local Python runtime only.

## Red

The Windows environment does not expose `python` on `PATH`, so the equivalent
local runtime invocation was used:

```powershell
& 'C:\Users\60388\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest tests.test_governance_tools -v
```

Before implementation it failed during test import with:

```text
ModuleNotFoundError: No module named 'patchpilot'
```

## Green

The same command passed after implementing `Workspace`, `Guardrail`,
`ApprovalStore`, and `ToolRegistry`:

```text
Ran 6 tests in 0.076s
OK (skipped=1)
```

The skipped assertion verifies an external symbolic-link escape. Windows on
this host does not permit creating symbolic links for the test process; path
traversal and absolute-path rejection still execute. The implementation also
checks resolved paths so the case is covered where symlink creation is allowed.

The exercised behavior includes path traversal/absolute path containment,
atomic overwrite, dangerous command and shell-interpreter denial, whitelist
enforcement, content-bound one-time approval replay protection, and bounded
shell-free command output.
