# 最终交付索引

本页把课程清单逐项映射到可核验文件。`已完成`只表示仓库内证据已就绪；涉及学生身份、课程账号或个人观点的项目不会由自动化伪造完成。

| # | 交付项 | 状态 | 仓库证据 / 操作 |
|---|---|---|---|
| 1 | SPEC、PLAN、SPEC_PROCESS | 已完成 | `SPEC.md`、`PLAN.md`、`SPEC_PROCESS.md` |
| 2 | 完整源码与规范提交历史 | 已完成（GitHub） | <https://github.com/GuKongZhiMeng/patchpilot>；`src/`、`tests/`、`deploy-web/`；`git log --oneline --all` |
| 3 | 分发产物 | 已完成 | `Dockerfile`、`pyproject.toml`；最终 wheel、源码 zip、Git bundle 输出到 `../outputs/` |
| 4 | README 必备章节 | 已完成 | `README.md`：项目简介、安装、运行、分发命令、目录结构、安全边界、已知限制 |
| 5 | Agent 日志 | 已完成 | `AGENT_LOG.md`，并由提交历史和 `docs/*_TDD.md` 交叉验证 |
| 6 | GitLab CI，含 unit-test job | 已完成 | `.gitlab-ci.yml`：`unit-test`、`web-unit-test`、`docker-build` |
| 7 | CI/CD 最终通过记录 | 已完成（GitHub Actions） | `CI_CD_RECORD.md`；PR #1、最终 PR #2 与最新 `master` workflow 均要求 3/3 检查通过 |
| 8 | 1500–2500 字反思 | 已完成，待学生最终逐句确认 | `REFLECTION.md`；核心观点与原始问答由学生提供，AI 事实校验与润色已在文末披露 |
| 9 | 线上部署 URL 与 WebUI | 已完成（公开） | <https://patchpilot-agent-harness.sturdy-angel-7006.chatgpt.site>；源码位于 `deploy-web/`，评分者可直接访问 |
| A | 自实现 harness 内核 | 已完成 | `src/patchpilot/engine.py`、`models.py`、`tools.py`、`guardrails.py`、`feedback.py`、`memory.py` |
| A | mock-LLM 单元测试 | 已完成 | `tests/test_engine.py` 等离线确定性测试 |
| A | 机制演示 | 已完成 | `python -m patchpilot demo`；部署 WebUI 的交互式机制实验台 |

## 已知流程偏离与最终人工确认

1. 学生须在上传前逐句确认 `REFLECTION.md` 确实表达本人观点，并保留 AI 辅助声明。
2. 早期 worktree 在建立远端前完成，没有逐一对应真实 PR；仓库不补造回溯性 PR，详见 `MR_PR_RECORD.md`。
3. 本次开发会话没有安装 Superpowers 插件；仓库只陈述方法参考。这是无法通过补写日志消除的流程偏离。

提交前还应执行 `git grep` 与历史扫描，确认无真实 key、token、`.env` 或个人敏感信息。

MR/PR 的诚实完成路径与本地分支证据见 `MR_PR_RECORD.md`。
