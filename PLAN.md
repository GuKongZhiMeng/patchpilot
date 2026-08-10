# PatchPilot 实现计划

状态约定：`[ ]` 未开始，`[x]` 完成。每项先写失败测试，再写最小实现，最后重构。

## 依赖图

T1 → T2 → T5；T1 → T3 → T5；T1 → T4 → T5；T5 → T6 → T7。T2/T3/T4 可在独立 worktree 并行。

## Tasks

- [x] **T1 基础模型、配置与 LLM 端口** — `3562163`
  - 文件：`src/patchpilot/models.py`、`config.py`、`llm.py`、`tests/test_config_llm.py`
  - 测试先行：非法动作/未知配置失败，scripted LLM 记录输入，HTTP adapter 严格解析。
  - 验证：`python -m unittest tests.test_config_llm -v`。

- [x] **T2 工作区工具与治理状态机**（依赖 T1，可与 T3/T4 并行）— `e5d5c1d`，review 修订 `246e3e2`
  - 文件：`workspace.py`、`guardrails.py`、`tools.py`、`tests/test_governance_tools.py`
  - 测试先行：路径穿越、危险命令、shell 元字符、审批重放、允许命令、原子写。
  - 验证：`python -m unittest tests.test_governance_tools -v`。

- [x] **T3 验证器与深度反馈闭环**（依赖 T1，可并行）— `1002963`，review 修订 `246e3e2`
  - 文件：`feedback.py`、`tests/test_feedback.py`
  - 测试先行：分类、ANSI 清理、截断、指纹稳定、重复失败熔断、通过后复位。
  - 验证：`python -m unittest tests.test_feedback -v`。

- [x] **T4 SQLite 记忆与事件**（依赖 T1，可并行）— `697aa21`
  - 文件：`memory.py`、`events.py`、`tests/test_memory.py`
  - 测试先行：隔离、相关性排序、数量限制、敏感字段拒绝。
  - 验证：`python -m unittest tests.test_memory -v`。

- [x] **T5 主循环集成**（依赖 T2/T3/T4）— `d4f4387`，HITL 修订 `246e3e2`
  - 文件：`engine.py`、`tests/test_engine.py`
  - 测试先行：非法动作回灌、写后验证、失败后改变动作、终检、预算与停机。
  - 验证：`python -m unittest tests.test_engine -v`。

- [x] **T6 CLI、凭据与机制演示**（依赖 T5）— `0b0d413`，review 修订 `246e3e2`
  - 文件：`credentials.py`、`cli.py`、`scripts/mechanism_demo.py`、相关测试。
  - 测试先行：key 不回显、secret 文件权限、三段 mock 演示输出。
  - 验证：`python -m patchpilot demo` 与单测。

- [x] **T7 WebUI、分发与文档**（依赖 T6）— `0b0d413`，UI/review 修订 `246e3e2`
  - 文件：`web.py`、`web/index.html`、`Dockerfile`、`.gitlab-ci.yml`、`README.md`、`AGENT_LOG.md`、`REFLECTION.md`。
  - 测试先行：健康检查、安全头、输入校验；CI job 必须名为 `unit-test`。
  - 验证：全量单测、demo、包构建、Docker build（若本机 Docker 可用）。

## 冷启动门槛

在任何实现代码之前，把仅有 `SPEC.md` 与 `PLAN.md` 的上下文交给无历史、不同配置的 agent，让其选择 T1/T2 的测试设计并指出歧义；记录问题和修订 diff 到 `SPEC_PROCESS.md`。

## 提交与 PR 计划

本地按 `docs(spec/plan)`、`feat(core)`、`feat(feedback)`、`feat(ui-distribution)` 分段 commit。NJU Git 上按 T2/T3/T4 建 worktree/分支与 PR；由于当前没有远端和账号，不伪造 PR 或 CI 记录，推送后由学生补充 URL、PR 编号和最终 pass 截图。
